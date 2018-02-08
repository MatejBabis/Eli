import GPy
from dataset_processing import *
import spotify

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

#####################################
# O F F L I N E   A L G O R I T H M #
#####################################


# read in the dataset from a file
data = read_stored_data('library_trimmed.data')

trackPairs = []

tracksSeen = []
Xnew = np.zeros((1, 2 * 25))
Ynew = np.array([0])

for i in range(10):
    ## Offline
    # t1 = generateNewTrackOffline(data, tracksSeen)
    # t2 = generateNewTrackOffline(data, tracksSeen)

    tracks = getTracks(data, tracksSeen)
    t1 = tracks[0][0]
    t2 = tracks[1][0]
    t1_url = tracks[0][1]
    t2_url = tracks[1][1]
    t1_attr = getAttributes(t1)
    t2_attr = getAttributes(t2)

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))

    print "Say which of these two you prefer:"

    print "0: '" + t1[2] + "' by " + t1[1]
    playTrack(t1_url)

    print "1: '" + t2[2] + "' by " + t2[1]
    playTrack(t2_url)

    print "> ",
    preference = int(raw_input())

    if preference is 0:
        preference = 1
    elif preference is 1:
        preference = -1
    else:
        print "Fucked it."
        exit()

    ## Offline
    # Ynew = np.vstack((Ynew, np.random.choice([-1, 1])))

    Ynew = np.vstack((Ynew, preference))
    tracksSeen.extend((t1, t2))     # remove for Offline

    trackPairs += [(t1[2], t2[2])]

Ytrain = Ynew[1:]
Xtrain = Xnew[1:]

#########
# T E S T
#########

testPairs = []
Xnew = np.zeros((1, 2 * 25))
for i in range(1, len(data)):
    t1_attr = getAttributes(data[i-1])
    t2_attr = getAttributes(data[i])

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))
    testPairs += [(data[i-1][2], data[i][2])]

Xtest = Xnew[1:]

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

cumsum = np.cumsum(E_fstar)
# everything is calibrated with respect to 0, so prepend 0
cumsum = np.insert(cumsum, 0, 0, axis=0)
print cumsum

maximum_index = np.argmax(cumsum)
print cumsum[maximum_index]
print data[maximum_index][2]
print

winner = data[maximum_index]
winner_url = spotify.querySpotifyUrl(winner)
playTrack(winner_url)


p_ystar_xstar, dum = m.predict(Xtest, full_cov=False)

dec = np.hstack((testPairs, p_ystar_xstar))

print "Matrix holding the X, Y, p(y=1|x) for the test points"
print dec
