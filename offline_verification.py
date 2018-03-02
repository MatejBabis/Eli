"""
This file takes only two of the song features and creates a model based on
if the second feature for t1 is larger than second feature for t2.
Just a proof of correctness for the algorithm.
"""

import GPy
from dataset_processing import *
import spotify
from sklearn.metrics import confusion_matrix
from matplotlib import pyplot as plt
import vlc
import time

# get song attributes as a vector
def getAttributes(track):
    t_pitch = track[3]
    t_timbre = track[4]
    t_loud = track[5]
    return np.hstack((t_pitch, t_timbre, t_loud))


# play track from the specified url
def playTrack(url):
    p = vlc.MediaPlayer(url)
    p.play()
    time.sleep(5)  # playtime in seconds
    p.stop()


# pick a previously unseen random track
def generateNewTrack(dataset, listOfTracks):
    track = dataset[int(np.random.rand() * len(dataset))]
    while track in listOfTracks:
        track = dataset[int(np.random.rand() * len(dataset))]
    return track


# choose two random tracks with 2 conditions:
#   1: make sure user hasn't rated any of them yet
#   2: make sure they exist on Spotify
# returns a tuple of tuples containing 2 tracks, each of which
# is a tuple consisting of metadata and Spotify url
def getTracks(dataset, listOfTracks):
    track1 = generateNewTrack(dataset, listOfTracks)
    track2 = generateNewTrack(dataset, listOfTracks)

    track1_url = spotify.querySpotifyUrl(track1)
    track2_url = spotify.querySpotifyUrl(track2)

    # loop if & until a Spotify-friendly tracks are found
    while (track1_url is None) or (track1[2] is track2[2]):
        track1 = generateNewTrack(dataset, listOfTracks)
        track1_url = spotify.querySpotifyUrl(track1)
    listOfTracks += [track1]

    # also make sure we are not comparing the same songs
    while (track2_url is None) or (track2[2] is track1[2]):
        track2 = generateNewTrack(dataset, listOfTracks)
        track2_url = spotify.querySpotifyUrl(track2)
    listOfTracks += [track2]

    return (track1, track1_url), (track2, track2_url)

# Offline equivalent of the function above so that we don't
# have to query Spotify
def generateNewTrackOffline(dataset, listOfTracks):
    track = dataset[int(np.random.rand() * len(dataset))]
    while track in listOfTracks:
        track = dataset[int(np.random.rand() * len(dataset))]
    listOfTracks += [track]
    return track







# read in the dataset from a file
data = read_stored_data('library_trimmed.data')

trackPairs = []

tracksSeen = []
Xnew = np.zeros((1, 2))
Ynew = np.array([0])

for i in range(10):
    t1 = generateNewTrackOffline(data, tracksSeen)
    t2 = generateNewTrackOffline(data, tracksSeen)
    t1_attr = getAttributes(t1)
    t2_attr = getAttributes(t2)
    t1_attr = t1_attr[:1]
    t2_attr = t2_attr[:1]

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))

    if t1_attr[0] > t2_attr[0]:
        Ynew = np.vstack((Ynew, 0))
    else:
        Ynew = np.vstack((Ynew, 1))

    tracksSeen.extend((t1, t2))     # remove for Offline

    trackPairs += [(str(t1_attr), str(t2_attr))]

Ytrain = Ynew[1:]
Xtrain = Xnew[1:]

#########
# T E S T
#########

testPairs = []
Xnew = np.zeros((1, 2))
Ynew = np.array([0])

for i in range(1, len(data)):
    t1_attr = getAttributes(data[i-1])
    t2_attr = getAttributes(data[i])
    t1_attr = t1_attr[:1]
    t2_attr = t2_attr[:1]

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))

    if t1_attr[0] > t2_attr[0]:
        Ynew = np.vstack((Ynew, 0))
    else:
        Ynew = np.vstack((Ynew, 1))

    testPairs += [(str(t1_attr), str(t2_attr))]

Xtest = Xnew[1:]
Ytest = Ynew[1:]

likelihood = GPy.likelihoods.Bernoulli()
laplace_inf = GPy.inference.latent_function_inference.Laplace()

# we use a PJK kernel with RBF base,
# i.e. a length scale and a variance parameter
kernel = GPy.kern.PjkRbf(Xtrain.shape[1])
kernel.variance = np.sqrt(2)
kernel.lengthscale = 0.5

# Model definition
m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood,
                inference_method=laplace_inf)

print m

E_fstar, V_fstar = m.predict_f(Xtest, full_cov=True)

p_ystar_xstar, dum = m.predict(Xtest, full_cov=False)

dec = np.hstack((testPairs, p_ystar_xstar))

print "Matrix holding the X, Y, p(y=1|x) for the test points"
print dec

# Plot the eval function
fig, axes = plt.subplots(1, 1)
fig.suptitle(
    'Predictive mean for f which is a difference: $\mathbb{E}(f(x^*))$', fontsize=20)
fig.set_size_inches(2.54 * 3., 2.54 * 3.)
plt.plot(E_fstar)
plt.show()

fig, axes = plt.subplots(1, 1)
fig.set_size_inches(2.54 * 3., 2.54 * 3.)
fig.suptitle(
    'Predictive mean for the sliced: $\mathbb{E}(f_{sliced}(x^*))$', fontsize=20)
axes.set_xlabel('$x$', fontsize=16)
axes.set_ylabel('$f(x)$', fontsize=16)
for i in range(0, 10):
    plt.plot(E_fstar[0 + i * 10:10 + i * 10], label='Line 2')

plt.show()

# Probablistic predictions
fig, axes = plt.subplots(1, 1)
fig.suptitle('$p(y^*|x^*)$', fontsize=20)
axes.set_xlabel('Index of, $x^*$, i.e. a comparison', fontsize=16)
axes.set_ylabel('$p(y^*|x^*)$', fontsize=16)
fig.set_size_inches(2.54 * 3., 2.54 * 3.)
im = plt.plot(p_ystar_xstar)
plt.show()


# Confusion matrix
Ypred = p_ystar_xstar > 0.5
for i in range(len(Ytest)):
    if Ytest[i] == -1:
        Ytest[i] = 0

a = confusion_matrix(Ytest, Ypred)

print a