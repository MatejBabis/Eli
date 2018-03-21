# The machine learning model

import dataset_processing

import numpy as np
import GPy
import logging
from sys import stdout
import time

log = logging.getLogger("Eli.model")
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)


class Model:
    def __init__(self):
        log.info("Initialising new instance.")

        np.random.seed(1337)  # to ensure shuffling is constant for all users

        data = dataset_processing.alternative_read_stored_data("final_data_standardized")

        # store what genre each track is
        trackGenres = dataset_processing.store_track_and_genre(data)

        # split data into training and testing sets
        # that have each genre represented by 10 tracks
        trainSet, testSet = dataset_processing.create_datasets(data)

        # shuffle the tracks within the sets
        np.random.shuffle(trainSet)
        np.random.shuffle(testSet)

        ###########################
        # Training data processing

        _, _, trainPairs, duplicatePairs = dataset_processing.create_training_data(trainSet)

        # shuffle these pairs as well so that
        # we don't present them as linked list
        np.random.shuffle(trainPairs)

        self.trainPairs = trainPairs
        self.seenPairs = []
        self.testSet = testSet
        self.trackGenres = trackGenres          # what genre each track is
        self.Xtrain = np.zeros((1, 2 * 50))
        self.Ytrain = np.array([0])
        self.elicitationFinished = False        # flag to denote that model building has begun
        self.recommendationsReady = False
        self.elicitationStartTime = None        # for evaluation, time the first pair was presented
        self.trackStartTime = None
        self.cumAssessmentTime = 0
        self.recommendations = []               # use this for production (change interface.py line 41)
        # self.experimentRecommendations = []   # use this for evaluation (change interface.py line 41)
        # self.duplicatePairs = duplicatePairs  # for evaluation
        # self.duplicatePairFlag = False        # for evaluation

        log.info("Instance initialised.")

    def rate_pair(self, preference):
        if preference is 0 or preference is 1:
            self.Ytrain = np.vstack((self.Ytrain, preference))

            # Only for evaluation
            # if self.duplicatePairFlag is True:
            #     log.info("THIS IS A DUPLICATE PAIR")
            #     self.duplicatePairFlag = False

            return True
        else:
            return False

    # Process the data in the training set by presenting it to a user
    def return_track_info(self):

        # set the time during the first run
        if self.elicitationStartTime is None:
            self.elicitationStartTime = time.time()
        # set the evaluation time for each pair
        self.trackStartTime = time.time()

        pair = self.trainPairs.pop(0)

        # Only for evaluation
        # to be used by the rate_pair function:
        # this odd comparison approach has to be used due to a bug in numpy
        # for i in range(len(self.duplicatePairs)):
        #     if np.array_equal(self.duplicatePairs[i][0],pair[0]) and \
        #             np.array_equal(self.duplicatePairs[i][1], pair[1]):
        #         self.duplicatePairFlag = True
        #         break

        self.seenPairs += [pair]

        t1_meta = pair[0]
        t1_attr = pair[1]
        t2_meta = pair[2]
        t2_attr = pair[3]
        t1_url = t1_meta[3]
        t2_url = t2_meta[3]

        self.Xtrain = np.vstack((self.Xtrain, np.hstack((t1_attr, t2_attr))))

        t1_dsc = "'" + t1_meta[2] + "' by " + t1_meta[1]
        t2_dsc = "'" + t2_meta[2] + "' by " + t2_meta[1]

        return (t1_dsc, t1_url), (t2_dsc, t2_url)

    @staticmethod
    def hyperparameter_optimization(kernel, likelihood, inference, Xtrain, Ytrain):
        # dimensions of the matrix that will hold hyperparameter
        # values within range (1:10)
        dimension = np.arange(1.0, 10.0, 0.25)
        # arbitrary large values
        minimum = 9999
        min_l = 999
        min_v = 999

        for l in dimension:
            for v in dimension:
                kernel.lengthscale = l
                kernel.variance = v

                m = GPy.core.GP(Xtrain, Ytrain, kernel=kernel, likelihood=likelihood, inference_method=inference)
                if -m.log_likelihood() < minimum:
                    minimum = -m.log_likelihood()
                    min_l = l
                    min_v = v

        log.info("Hyperparameter optimization completed.")
        log.info("Minimum log likelihood estimation: %s", str(minimum))
        log.info("Resulting parameter values:")
        log.info("lengthscale = %s, variance = %s", str(min_l), str(min_v))

        return min_l, min_v

    def recommendation(self):
        log.info("Beginning to build a model.")
        Xtest = np.zeros((1, 2 * 50))
        testSetAttr = self.testSet[:, 4:].astype(float)

        # Create a chained list for the testing data
        for i in range(1, len(testSetAttr)):
            t1_attr = testSetAttr[i - 1]
            t2_attr = testSetAttr[i]

            Xtest = np.vstack((Xtest, np.hstack((t1_attr, t2_attr))))

        Xtest = Xtest[1:]

        # we use a PJK kernel with RBF base
        kernel = GPy.kern.PjkRbf(self.Xtrain.shape[1])
        likelihood = GPy.likelihoods.Bernoulli()
        laplace_inf = GPy.inference.latent_function_inference.Laplace()

        # we perform hill climbing to select the hyperparameter values
        l, v = self.hyperparameter_optimization(kernel, likelihood, laplace_inf,
                                                self.Xtrain, self.Ytrain)

        # assign the resulting hyperparameters
        kernel.variance = v
        kernel.lengthscale = l

        # build a model
        m = GPy.core.GP(self.Xtrain, self.Ytrain,
                        kernel=kernel, likelihood=likelihood,
                        inference_method=laplace_inf)

        log.info("Model built!")

        # RECOMMENDATION
        log.info("Generating recommendations.")

        E_fstar, _ = m.predict_f(Xtest, full_cov=True)

        # Compute delta values for each prediction
        cumsum = np.cumsum(E_fstar)
        # everything is calibrated with respect to 0, so prepend 0
        cumsum = np.insert(cumsum, 0, 0, axis=0)

        # create (Track, Delta) tuples
        delta_track = []
        for i in range(len(cumsum)):
            delta_track += [(self.testSet[i][:4], cumsum[i])]
        # sort the list based on the delta
        delta_track.sort(key=lambda x: x[1], reverse=True)

        # return top 5 recommendations
        recommendations = []
        log.info("\nAll recommendations:")
        for i in range(len(delta_track)):
            # return top 5 recommendations
            if i < 5:
                recommendations += [(delta_track[i][0][1] + " - " + delta_track[i][0][2], delta_track[i][0][3])]
            # log everything
            log.info("%s - %s", delta_track[i][0][1], delta_track[i][0][2])
            log.info("\tGenre: %s", self.trackGenres[delta_track[i][0][0]])
            log.info("\tDelta: %s", str(delta_track[i][1]))

        # # for the experiment, also include 5 tracks that have mean deltas
        # # i.e. the user doesn't love them nor hate them
        # experimentRecommendations = []
        # middleRange = range(int(len(delta_track)/2) - 2, int(len(delta_track)/2) + 3)
        # for i in middleRange:
        #     experimentRecommendations += [(delta_track[i][0][1] + " - " + delta_track[i][0][2], delta_track[i][0][3])]
        #
        # # add the original recommendations
        # experimentRecommendations += recommendations
        #
        # # print them as well
        # log.info("\nExperimental 'recommendations' (not in the order presented):")
        # for i in range(len(experimentRecommendations)):
        #     log.info("%s", experimentRecommendations[i][0])
        #
        # # shuffle the list so that it's not obvious
        # np.random.shuffle(experimentRecommendations)

        self.recommendationsReady = True
        self.recommendations = recommendations
        # self.experimentRecommendations = experimentRecommendations


if __name__ == '__main__':
    Model()
