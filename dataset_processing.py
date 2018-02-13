import glob
import numpy as np
import os
import pickle
import sys

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
import hdf5_getters as GETTERS   # noqa


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
        for f in files:
            complete_data += [func(f)]

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

    # TODO: REMOVE
    print foo.counter
    foo()

    track_id = GETTERS.get_track_id(h5)
    artist = GETTERS.get_artist_name(h5)
    title = GETTERS.get_title(h5)
    pitches = GETTERS.get_segments_pitches(h5)
    timbre = GETTERS.get_segments_timbre(h5)
    loudness = GETTERS.get_segments_loudness_max(h5)

    data = [track_id,
            artist,
            title,
            # mean for each column in pitches
            map(np.mean, zip(*pitches)),
            # same for timbre
            map(np.mean, zip(*timbre)),
            # and average value for max_loudness
            np.mean(loudness)
            ]

    h5.close()

    return data


def genre_processing_func(filename):
    h5 = GETTERS.open_h5_file_read(filename)

    track_id = GETTERS.get_track_id(h5)
    artist = GETTERS.get_artist_name(h5)
    title = GETTERS.get_title(h5)
    song_hotttnesss = GETTERS.get_song_hotttnesss(h5)

    data = [track_id,
            artist,
            title,
            song_hotttnesss]

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
    print "Dataset succesfully loaded."
    return dataset
