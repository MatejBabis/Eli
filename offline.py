import GPy
from dataset_processing import *
import spotify
from sklearn import preprocessing

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


#####################################
# O F F L I N E   A L G O R I T H M #
#####################################

# # read in the old dataset from a file
# data = read_stored_data('library.data')

# run this if hotttnesss dataset has changed
# generate_hot_examples(data)

trainingDataset = read_stored_data('hot_training_set.data')     # query the user on this
testingDataset = read_stored_data('hot_testing_set.data')       # give recommendation from this
hotTrackUrls = read_stored_data('hot_track_urls.data')          # corresponding ID : URL pairs
hotTrackGenres = read_stored_data("hot_track_genres.data")      # corresponding ID : Genre pairs

# This block is just because of the data normalisation,
# FIXME: Will be done in pre-processing and therefore removed
dataset = trainingDataset + testingDataset
dataset_attr = np.zeros((1, 25))
for track in dataset:
    track_attr = getAttributes(track)
    dataset_attr = np.vstack((dataset_attr, np.hstack(track_attr)))
# standardize the inputs, i.e. scaled data now has 0 mean and unit variance
dataset_attr = preprocessing.scale(dataset_attr[1:])
trainingDataset_attr = dataset_attr[:50]
testingDataset_attr = dataset_attr[50:]
for i in range(len(trainingDataset)):
    trainingDataset[i] = [trainingDataset[i][0], trainingDataset[i][1], trainingDataset[i][2], trainingDataset_attr[i]]
for i in range(len(testingDataset)):
    testingDataset[i] = [testingDataset[i][0], testingDataset[i][1], testingDataset[i][2], testingDataset_attr[i]]

# This block is for testing - when we want to compare clusters of same genres
# FIXME: TEMPORARILY CLUSTER THE PAIRS INTO GENRES
# genre_dict = {"Pop_Rock": [], "Electronic": [],
#               "Rap": [], "Jazz": [], "RnB": []}
# for i in range(len(trainingDataset)):
#     genre_dict[hotTrackGenres[trainingDataset[i][0]]] += [trainingDataset[i]]
# trainingDataset = []
# for genre in genre_dict.keys():
#     for track in genre_dict[genre]:
#         trainingDataset += [track]
genre_dict = {"Pop_Rock": [], "Electronic": [],
              "Rap": [], "Jazz": [], "RnB": []}
for i in range(len(dataset)):
    genre_dict[hotTrackGenres[dataset[i][0]]] += [dataset[i]]
genre_dataset = np.zeros((1, 12))
dict_keys =  genre_dict.keys()
print dict_keys
for genre in dict_keys:
    for track in genre_dict[genre]:
        genre_dataset = np.vstack((genre_dataset, np.hstack((track[3]))))
genre_dataset = genre_dataset[1:]
# standardize the inputs, i.e. scaled data now has 0 mean and unit variance
dataset_attr = preprocessing.scale(genre_dataset[1:])

# store pairs seen in training phase
trainingPairs = []

Xnew = np.zeros((1, 2 * 25))
Ynew = np.array([0])

trainingSet = []
# generate pairs on the main diagonal
for i in range(1, len(trainingDataset)):
    trainingSet += [(trainingDataset[i-1], trainingDataset[i])]
# link the first one with the last one
trainingSet += [(trainingDataset[0], trainingDataset[len(trainingDataset)-1])]
# generate pairs on the 8-off diagonal
for i in range(8, len(trainingDataset)):
    trainingSet += [(trainingDataset[i-8], trainingDataset[i])]


# TODO: INCLUDE COUPLE OF PAIRS MULTIPLE TIMES, TO CHECK USER'S ABILITY TO RATE
for tuple in trainingSet:
    t1 = tuple[0]                   # track1
    t2 = tuple[1]                   # track2
    # t1_attr = getAttributes(t1)     # corresponding attributes
    # t2_attr = getAttributes(t2)
    t1_attr = t1[3]
    t2_attr = t2[3]

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))
    # User elicitation
    print "Say which of these two you prefer:"

    print "0: '" + t1[2] + "' by " + t1[1]
    # playTrack(hotTrackUrls[t1[0]])

    print "1: '" + t2[2] + "' by " + t2[1]
    # playTrack(hotTrackUrls[t2[0]])

    # Eliciting response from a user
    # while True:
    #     print "> ",
    #     userPreference = raw_input()
    #     if userPreference == "0" or userPreference == "1":
    #         break
    #     else:
    #         print "Not a valid preference. Try again"
    #         continue

    # automated response - always prefer tracks the tracks
    # with a genre appearing earlier in the list
    pref = ["Rap", "Pop_Rock", "Electronic", "Jazz", "RnB"]
    if pref.index(hotTrackGenres[t1[0]]) <= pref.index(hotTrackGenres[t2[0]]):
        userPreference = 0
    else:
        userPreference = 1
    print ">", str(userPreference)

    # store preference value (either 0 or 1)
    Ynew = np.vstack((Ynew, int(userPreference)))

    trainingPairs += [(t1[2], t2[2])]

Ytrain = Ynew[1:]
Xtrain = Xnew[1:]

#########
# T E S T
#########

testPairs = []

Xnew = np.zeros((1, 2 * 25))

# create a chained list for the testing data
for i in range(1, len(testingDataset)):
    # t1_attr = getAttributes(testingDataset[i-1])
    # t2_attr = getAttributes(testingDataset[i])
    t1_attr = testingDataset[i-1][3]
    t2_attr = testingDataset[i][3]

    Xnew = np.vstack((Xnew, np.hstack((t1_attr, t2_attr))))
    testPairs += [(testingDataset[i-1][2], testingDataset[i][2])]

Xtest = Xnew[1:]

likelihood = GPy.likelihoods.Bernoulli()
laplace_inf = GPy.inference.latent_function_inference.Laplace()

# we use a PJK kernel with RBF base,
# i.e. a length scale and a variance parameter
kernel = GPy.kern.PjkRbf(Xtrain.shape[1])
kernel.variance = 2.7
kernel.lengthscale = 2.4

m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood,
                inference_method=laplace_inf)
print m
print m.log_likelihood()

# This block tests increasing lengthscale parameter to find the converging value
from matplotlib import pyplot as plt
lengthscales = [1, 2, 2.5, 3.2]
for l in lengthscales:
    kernel.lengthscale = l
    k = kernel._RbfBase_K(dataset_attr)
    imgplot = plt.imshow(k)
    imgplot.set_interpolation('none')
    plt.text(10, 80, "lengthscale: " + str(l), bbox=dict(facecolor='white', alpha=0.5))
    plt.show()
    # # Model definition
    # m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood,
    #                 inference_method=laplace_inf)
    # # print m
    # print temp, m.log_likelihood()
    # # print


#TODO: CROSS-VALIDATION

results = []

E_fstar, V_fstar = m.predict_f(Xtest, full_cov=True)

cumsum = np.cumsum(E_fstar)
# everything is calibrated with respect to 0, so prepend 0
cumsum = np.insert(cumsum, 0, 0, axis=0)

# create (Track, Delta) tuples
delta_track = []
for i in range(len(cumsum)):
    delta_track += [(testingDataset[i], cumsum[i])]

# sort the list based on the delta
delta_track.sort(key=lambda x: x[1], reverse=True)
# print the 10 most popular ones
print "\nRecommendations:"
for i in range(10):
    print delta_track[i][0][1] + " " + delta_track[i][0][2],    # name
    print "    Genre: " + hotTrackGenres[delta_track[i][0][0]], delta_track[i][1]

    # play the track
    # url = spotify.querySpotifyUrl(delta_track[i][0])
    # playTrack(url)

# p_ystar_xstar, dum = m.predict(Xtest, full_cov=False)
#
# dec = np.hstack((testPairs, p_ystar_xstar))
#
# print "Matrix holding a Pair of songs and associated p(y=1|x)"
# print dec
