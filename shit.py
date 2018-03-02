import glob
import os
import sys
import numpy as np

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
    counter = 0

    complete_data = []
    # iterate over all files in all subdirectories
    for root, dirs, files in os.walk(basedir):
        files = glob.glob(os.path.join(root, '*' + ext))

        # apply function to all files
        for f in files:
            counter += len(files)
            try:
                complete_data += [func(f)]
            except:
                print "Couldn't read file: ", f
                continue
        if counter > 1:
            break

    return complete_data


def func_to_extract_track_info(filename):
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


def alternative_store_data_in_file(l, filename):
    np.save(filename, l)


def alternative_read_stored_data(filename):
    dataset = np.load(filename + ".npy")
    print "File '" + filename + ".npy' successfully loaded."
    return dataset

f = open("all.txt", 'r')
lines = f.readlines()
f.close()
track_ids = []
for l in lines:
    track_ids += [l[:-1]]

data = apply_to_all_files(msd_subset_path, func_to_extract_track_info)

alternative_store_data_in_file(data, "shit")

data = alternative_read_stored_data("shit")

for d in data:
    print d