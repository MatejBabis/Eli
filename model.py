from dataset_processing import *
import spotify

import vlc
import time


class Interface:
    def __init__(self):
        self.data = read_stored_data('library_20.data')
        self.trackPairs = []
        self.tracksSeen = []
        self.Xtrain = np.zeros((1, 2 * 25))
        self.Ytrain = np.array([0])

    # get song attributes as a vector
    def getAttributes(self, track):
        t_pitch = track[3]
        t_timbre = track[4]
        t_loud = track[5]
        return np.hstack((t_pitch, t_timbre, t_loud))

    # play track from the specified url
    def playTrack(self, url):
        p = vlc.MediaPlayer(url)
        p.play()
        time.sleep(1)  # playtime in seconds
        p.stop()

    # pick a previously unseen random track
    def generateNewTrack(self, dataset, listOfTracks):
        track = dataset[int(np.random.rand() * len(dataset))]
        while track in listOfTracks:
            track = dataset[int(np.random.rand() * len(dataset))]
        return track

    # choose two random tracks with 2 conditions:
    #   1: make sure user hasn't rated any of them yet
    #   2: make sure they exist on Spotify
    # returns a tuple of tuples containing 2 tracks, each of which
    # is a tuple consisting of metadata and Spotify url
    def getTracks(self, dataset, listOfTracks):
        track1 = self.generateNewTrack(dataset, listOfTracks)
        track2 = self.generateNewTrack(dataset, listOfTracks)

        track1_url = spotify.querySpotifyUrl(track1)
        track2_url = spotify.querySpotifyUrl(track2)

        # loop if & until a Spotify-friendly tracks are found
        while (track1_url is None) or (track1[2] is track2[2]):
            track1 = self.generateNewTrack(dataset, listOfTracks)
            track1_url = spotify.querySpotifyUrl(track1)
        listOfTracks += [track1]

        # also make sure we are not comparing the same songs
        while (track2_url is None) or (track2[2] is track1[2]):
            track2 = self.generateNewTrack(dataset, listOfTracks)
            track2_url = spotify.querySpotifyUrl(track2)
        listOfTracks += [track2]

        return (track1, track1_url), (track2, track2_url)

    def returnTrackInfo(self):
        tracks = self.getTracks(self.data, self.tracksSeen)
        t1 = tracks[0][0]
        t2 = tracks[1][0]
        t1_url = tracks[0][1]
        t2_url = tracks[1][1]
        t1_attr = self.getAttributes(t1)
        t2_attr = self.getAttributes(t2)

        self.Xtrain = np.vstack((self.Xtrain, np.hstack((t1_attr, t2_attr))))

        t1_dsc = "'" + t1[2] + "' by " + t1[1]
        t2_dsc = "'" + t2[2] + "' by " + t2[1]

        # print "Say which of these two you prefer:"
        #
        # print "0:", t1_dsc
        # # playTrack(t1_url)
        #
        # print "1:", t2_dsc
        # # playTrack(t2_url)
        #
        # print "> ",
        # preference = int(raw_input())
        #
        # if preference is 0:
        #     preference = 1
        # elif preference is 1:
        #     preference = -1
        # else:
        #     print "Fucked it."
        #     exit()
        #
        # self.Ytrain = np.vstack((self.Ytrain, preference))

        self.trackPairs += [(t1[2], t2[2])]

        return (t1_dsc, t1_url), (t2_dsc, t2_url)
    
    def ratePair(self, preference):
        if preference is 0 or preference is 1:
            self.Ytrain = np.vstack((self.Ytrain, preference))
            return True
        else:
            return False


if __name__ == '__main__':
    Interface().returnTrackInfo()
