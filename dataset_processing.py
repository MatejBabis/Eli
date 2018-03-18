# This dataset is used to generate and access values from the dataset.
# Heavy inspiration from the example functions provided by MSD authors.

# Some of these functions were only used once in the generation process
# and are not invoked anymore. However, they provide good evidence
# of how the data was created.

import glob
import numpy as np
import os
import pickle
import sys
from sklearn import preprocessing

# path to the Million Song Dataset subset (uncompressed)
msd_subset_path = '/Volumes/Alakazam/_l4p/MillionSongSubset'
msd_subset_data_path = os.path.join(msd_subset_path, 'data')
msd_subset_addf_path = os.path.join(msd_subset_path, 'AdditionalFiles')
assert os.path.isdir(msd_subset_path), 'wrong path'  # sanity check
# path to the Million Song Dataset code
msd_code_path = '/Volumes/Alakazam/_l4p/MSongsDB'
assert os.path.isdir(msd_code_path), 'wrong path'  # sanity check

# adding paths to python so we can import MSD code
sys.path.append(os.path.join(msd_code_path, 'PythonSrc'))

# imports specific to the MSD
import hdf5_getters as GETTERS


def apply_to_all_files(basedir, func=lambda x: x, ext='.h5'):
    # Iterate all files
    """
    From a base directory, go through all subdirectories,
    find all files with the given extension, apply the
    given function 'func' to all of them.
    INPUT
       basedir  - base directory of the dataset
       func     - function to apply to all filenames
       ext      - extension, .h5 by default
    """

    complete_data = []
    # iterate over all files in all subdirectories
    for root, dirs, files in os.walk(basedir):
        files = glob.glob(os.path.join(root, '*' + ext))

        # apply function to all files
        for track in files:
            try:
                complete_data += [func(track)]
            except:
                print "Couldn't read file: ", track
                continue

    return complete_data


def func_to_extract_data_all(filename):
    # we define the function to apply to all files
    """
    This function does 4 simple things:
    - open the song file
    - get selected data
    - close the file
    - return the data
    """

    h5 = GETTERS.open_h5_file_read(filename)

    track_id = GETTERS.get_track_id(h5)
    artist = GETTERS.get_artist_name(h5)
    title = GETTERS.get_title(h5)
    pitches = GETTERS.get_segments_pitches(h5)
    timbre = GETTERS.get_segments_timbre(h5)
    loudness = GETTERS.get_segments_loudness_max(h5)

    number_of_segments = len(pitches)

    # do not include information about the first and final 5%
    # of a track - these are often very different from the rest
    five_perc = int(number_of_segments * 0.05)

    p_mean = np.mean(pitches[five_perc:-five_perc], axis=0)
    p_std = np.std(pitches[five_perc:-five_perc], axis=0, ddof=1)
    t_mean = np.mean(timbre[five_perc:-five_perc], axis=0)
    t_std = np.std(timbre[five_perc:-five_perc], axis=0, ddof=1)
    l_mean = np.mean(loudness[five_perc:-five_perc], axis=0)
    l_std = np.std(loudness[five_perc:-five_perc], axis=0, ddof=1)
    attr = np.hstack((p_mean, p_std, t_mean, t_std, l_mean, l_std))

    data = [track_id, artist, title] + attr.tolist()

    h5.close()

    return data


def store_data_in_file(l, filename):
    outputFile = filename
    fw = open(outputFile, 'wb')
    pickle.dump(l, fw)
    fw.close()


def read_stored_data(filename):
    fd = open(filename, 'rb')
    dataset = pickle.load(fd)
    print "File '" + filename + "' successfully loaded."
    return dataset


def alternative_read_stored_data(filename):
    dataset = np.load(filename + ".npy")
    print "File '" + filename + ".npy' successfully loaded."
    return dataset


def alternative_store_data_in_file(l, filename):
    np.save(filename, l)


# standardize data in the dataset - after called,
# each dimension of the attribute vector be spread according
# to normal distribution - as a result, each column has
# a zero mean and a unit variance
def standardize(data):
    return np.concatenate((
        data[:, :4],                                       # metedata - leave;
        preprocessing.scale(data[:, 4:].astype(float))),   # standardize the rest,
        axis=1)                                            # ensure it's a float


# compute what genre each track is
def store_track_and_genre(data):
    # genres in the order as they appear in the dataset
    genres = ["rap", "classical", "blues", "metal", "disco"]
    trackCounter = 0
    genreCounter = 0
    outputDict = {}
    for track in data:
        outputDict[track[0]] = genres[genreCounter]
        trackCounter += 1
        if trackCounter == 20:
            trackCounter = 0
            genreCounter += 1

    return outputDict


# split data into training and testing sets
# that have each genre represented by 10 tracks
def create_datasets(data):
    trainSet = np.zeros((1, 54))
    testSet = np.zeros((1, 54))
    for i in range(len(data)):
        if i % 2 == 0:
            trainSet = np.vstack((trainSet, np.hstack(data[i])))
        else:
            testSet = np.vstack((testSet, np.hstack(data[i])))
    trainSet = trainSet[1:]
    testSet = testSet[1:]
    return trainSet, testSet


def create_training_data(trainSet):
    trainSetAttr = trainSet[:, 4:].astype(float)
    trainSetMeta = trainSet[:, :4]
    trainPairs = []

    # generate pairs on the main diagonal
    for i in range(1, len(trainSetAttr)):
        trainPairs += [(trainSetMeta[i - 1], trainSetAttr[i - 1],
                        trainSetMeta[i], trainSetAttr[i])]

    # link the first song with the last song (i.e. add one more pair)
    trainPairs += [(trainSetMeta[0], trainSetAttr[0],
                    trainSetMeta[len(trainSetMeta) - 1], trainSetAttr[len(trainSetAttr) - 1])]

    # generate pairs on the 8-off diagonal
    for i in range(8, len(trainSetAttr)):
        trainPairs += [(trainSetMeta[i - 8], trainSetAttr[i - 8],
                        trainSetMeta[i], trainSetAttr[i])]

    # three random pairs were included two times in order to evaluate
    # if user responses are consistent
    duplicatePairs = []
    for i in np.random.choice(len(trainPairs), 3, replace=False):
        trainPairs += [trainPairs[i]]
        duplicatePairs += [trainPairs[i]]

    return trainSetAttr, trainSetMeta, trainPairs, duplicatePairs
