import numpy as np
import GPy
from matplotlib import pyplot as plt

import evaluation
import dataset_processing
import audio


# Eliciting response from a user
def elicit_preference(t1_meta, t2_meta, automated, pref):
    if automated is False:
        print "Say which of these two you prefer:"
        print "0: '" + t1_meta[2] + "' by " + t1_meta[1]
        audio.play_track(t1_meta[3])
        print "1: '" + t2_meta[2] + "' by " + t2_meta[1]
        audio.play_track(t2_meta[3])

    # Eliciting response from a user
    while automated is False:
        print "> ",
        userPreference = raw_input()
        if userPreference == "0" or userPreference == "1":
            break
        else:
            print "Not a valid preference. Try again"
            continue

    # automated response - always prefer tracks the tracks
    # with a genre appearing earlier in the list
    if automated is True:
        if pref.index(trackGenres[t1_meta[0]]) <= pref.index(trackGenres[t2_meta[0]]):
            userPreference = 0
        else:
            userPreference = 1

        # print ">", str(userPreference)

    return int(userPreference)


# Process the data in the training set by presenting it to a user
def process_training_data(trainPairs, pref, automated):
    Xtrain = np.zeros((1, 2 * 50))
    Ytrain = np.array([0])

    for i in range(len(trainPairs)):
        t1_meta = trainPairs[i][0]
        t1_attr = trainPairs[i][1]
        t2_meta = trainPairs[i][2]
        t2_attr = trainPairs[i][3]

        Xtrain = np.vstack((Xtrain, np.hstack((t1_attr, t2_attr))))

        # Eliciting response
        userPreference = elicit_preference(t1_meta, t2_meta, automated, pref)

        # store preference value (either 0 or 1)
        Ytrain = np.vstack((Ytrain, userPreference))

    return Xtrain[1:], Ytrain[1:]


# we perform hill climbing to select the hyperparameter values
def hyperparameter_optimization(kernel, likelihood, inference, evaluation, Xtrain, Ytrain):
    # dimensions of the matrix that will hold hyperparameter
    # values within range (1:10)
    dimension = np.arange(1.0, 10.0, 0.25)
    # arbitrary large values
    minimum = 9999
    min_l = 999
    min_v = 999

    if evaluation is True:
        hyper_values = np.empty((len(dimension), len(dimension)))

    for l in dimension:
        for v in dimension:
            kernel.lengthscale = l
            kernel.variance = v

            m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood, inference_method=inference)
            if -m.log_likelihood() < minimum:
                minimum = -m.log_likelihood()
                min_l = l
                min_v = v

            if evaluation is True:
                hyper_values[int(np.rint(l * 4)) - 4][int(np.rint(v * 4)) - 4] = -m.log_likelihood()

    print "\nHyperparameter optimization completed."
    print "Minimum log likelihood estimation:", str(minimum)
    print "Resulting parameter values:"
    print "\tlengthscale =", str(min_l) + ", variance =", str(min_v)

    if evaluation is True:
        plt.imshow(hyper_values)
        plt.show()

    return min_l, min_v


###########################################################################
#                      D R I V E R   F U N C T I O N                      #
###########################################################################

np.random.seed(1337)    # to ensure shuffling is constant for all users
evalMode = False         # enable for evaluation information

data = dataset_processing.alternative_read_stored_data("final_data_standardized")

# store what genre each track is
trackGenres = dataset_processing.store_track_and_genre(data)

evaluation.compute_kernel_matrix(data, evalMode)    # Evaluation only

# split data into training and testing sets
# that have each genre represented by 10 tracks
trainSet, testSet = dataset_processing.create_datasets(data)

# shuffle the tracks within the sets
np.random.shuffle(trainSet)
np.random.shuffle(testSet)

###########################
# Training data processing

trainSetAttr, trainSetMeta, trainPairs = dataset_processing.create_training_data(trainSet)

# shuffle these pairs as well so that
# we don't present them as linked list
np.random.shuffle(trainPairs)

print trainPairs[0][0][2], trainPairs[0][2][2]
print trainPairs[1][0][2], trainPairs[1][2][2]
print trainPairs[2][0][2], trainPairs[2][2][2]
exit()


###########################
# TRAINING PHASE

# Enable to automatically generate answers,
# as opposed to letting the user rank the pairs
automated = True
# Represent the order of preferences for automated responses
pref = ["rap", "metal", "disco", "blues", "classical"]

Xtrain, Ytrain = process_training_data(trainPairs, pref, automated)

###########################
# TESTING DATA GENERATION

Xtest = np.zeros((1, 2 * 50))
testSetAttr = testSet[:, 4:].astype(float)

# In case were doing evaluating, initiate data
# structures to hold true values for each pair
if evalMode is True:
    Ytest = np.array([0])
    testSetMeta = testSet[:, :4]
    testPairs = []

# Create a chained list for the testing data
for i in range(1, len(testSetAttr)):
    t1_attr = testSetAttr[i-1]
    t2_attr = testSetAttr[i]

    Xtest = np.vstack((Xtest, np.hstack((t1_attr, t2_attr))))

    # Compute true values for the evaluation
    if evalMode is True:
        t1_meta = testSetMeta[i - 1]
        t2_meta = testSetMeta[i]

        # Based on the preference scheme defined earlier, assign true values
        if pref.index(trackGenres[t1_meta[0]]) <= pref.index(trackGenres[t2_meta[0]]):
            userPreference = 0
        else:
            userPreference = 1

        # store preference value (either 0 or 1)
        Ytest = np.vstack((Ytest, int(userPreference)))

        # also store metadata about the pairs
        testPairs += [(t1_meta[1] + " - " + t1_meta[2], t2_meta[1] + " - " + t2_meta[2])]

Xtest = Xtest[1:]

if evalMode is True:
    Ytest = Ytest[1:]

###########################
# MODEL DEFINITION

# we use a PJK kernel with RBF base
kernel = GPy.kern.PjkRbf(Xtrain.shape[1])
likelihood = GPy.likelihoods.Bernoulli()
laplace_inf = GPy.inference.latent_function_inference.Laplace()

# we perform hill climbing to select the hyperparameter values
l, v = hyperparameter_optimization(kernel, likelihood, laplace_inf, evalMode, Xtrain, Ytrain)

# assign the resulting hyperparameters
kernel.variance = v
kernel.lengthscale = l

# build a model
m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood, inference_method=laplace_inf)

###########################
# RECOMMENDATION

E_fstar, _ = m.predict_f(Xtest, full_cov=True)

# Compute delta values for each prediction
cumsum = np.cumsum(E_fstar)
# everything is calibrated with respect to 0, so prepend 0
cumsum = np.insert(cumsum, 0, 0, axis=0)

# create (Track, Delta) tuples
delta_track = []
for i in range(len(cumsum)):
    delta_track += [(testSet[i][:4], cumsum[i])]
# sort the list based on the delta
delta_track.sort(key=lambda x: x[1], reverse=True)

# print top 10 recommendations
print "\nRecommendations:"
for i in range(10):
    # Artist - Track
    print delta_track[i][0][1] + " - " + delta_track[i][0][2]
    print "\tGenre: " + trackGenres[delta_track[i][0][0]]
    print "\tDelta: " + str(delta_track[i][1])

###########################
# EVALUATION MEASURES

if evalMode is True:
    p_ystar_xstar, _ = m.predict(Xtest, full_cov=False)

    # Pairwise preference prediction
    evaluation.pair_preference_prediction(testPairs, p_ystar_xstar)
    # Confusion Matrix
    evaluation.compute_confusion_matrix(Ytest, p_ystar_xstar)
    # Accuracy score
    print "\nAccuracy score:", evaluation.compute_accuracy_score(Ytest, p_ystar_xstar)
    # ROC Curve
    evaluation.compute_ROC_curve(Ytest, p_ystar_xstar)

    # Leave-one-out crossvalidation
    # Store track that was omitted and the resulting accuracy
    print "\n"
    LOO_accuracy = {}

    for track in trainSet:
        LOO_trainPairs = []

        # Remove all pairs that contain this particular track
        for pair in trainPairs:
            if track[0] != pair[0][0] and track[0] != pair[1][0]:
                LOO_trainPairs += [pair]

        LOO_Xtrain, LOO_Ytrain = process_training_data(LOO_trainPairs, pref, automated)

        # build a model
        m = GPy.core.GP(LOO_Xtrain, LOO_Ytrain, kernel=kernel, likelihood=likelihood, inference_method=laplace_inf)
        p_ystar_xstar, _ = m.predict(Xtest, full_cov=False)
        LOO_acc = evaluation.compute_accuracy_score(Ytest, p_ystar_xstar)

        LOO_accuracy[track[0]] = LOO_acc
        print "Accuracy without track '" + track[0] + "':", LOO_acc

    print "\nMean accuracy:", np.mean(LOO_accuracy.values())
