# This file contains functions relevant for audio playback

# Similarly to dataset_processing, majority of these functions
# were used during the dataset generation, but are no longer
# executed in order to increase the speed of the dataset
# - their output is now stored in files


import time
import vlc
from datetime import timedelta
import re
import numpy as np

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import dataset_processing


# play track from the specified url
def play_track(url):
    p = vlc.MediaPlayer(url)
    p.play()
    time.sleep(5)  # playtime in seconds
    p.stop()


def makeSpotifyQuery(req):
    # Get the parameter value from the JSON request
    result = req.get("result")
    parameters = result.get("parameters")

    if parameters.get("spotify-artist") is not None:
        artist = parameters.get("spotify-artist")
    else:
        return None

    if parameters.get("spotify-track") is not None:
        track = parameters.get("spotify-track")
    else:
        return None

    return {"track":track, "artist":artist}


# Transforms raw metadata into a dictionary form
def songsMetadata(searchResults, query):
    if searchResults is None or query is None:
        return {}

    resultList = searchResults["tracks"]["items"]
    output = []

    for song in resultList:
        # List all artists
        artists = ""
        for a in song["artists"]:
            artists += a["name"] + ", "
        artists = artists[:-2]

        # Track duration (assuming < 1hr)
        lengthMs = song["duration_ms"]
        length = str(timedelta(milliseconds=lengthMs))
        # Remove the unnecessary hours and remaining milliseconds
        length = length[2:].split('.')[0]

        output += [{
            "track": song["name"],
            "artist": artists,
            "album": song["album"]["name"],
            "length": length,
            "preview_url": song["preview_url"]
        }]
    return output


# search for track's sample url
def querySpotifyUrl(track):
    sp = instance

    artist = track[1]
    song = track[2]

    # construct Spotify query; remove things within brackets
    #   these usually mess up the search: things like e.g. "[Album version]"
    spotify_query = re.sub("[\(\[].*?[\)\]]", "", artist + " " + song)
    spotify_query_result = sp.search(q=spotify_query, type="track", limit=1, market="GB")

    # Check if song exists on Spotify
    if len(spotify_query_result["tracks"]["items"]) > 0:
        # get only relevant metadata
        metadata = songsMetadata(spotify_query_result, spotify_query)[0]

        # if a playable preview exists, return it
        if metadata["preview_url"] is not None:
            return metadata["preview_url"]
        else:
            return None
    else:
        return None

##########################################################
# THE FOLLOWING FUNCTIONS WERE USED TO EXTEND THE DATASET
# BY INCLUDING SPOTIFY URLS


def get_artist(name):
    results = instance.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None


def get_album_tracks(album, q_track):
    tracks = []
    results = instance.album_tracks(album['id'])

    # all album tracks
    tracks.extend(results['items'])
    while results['next']:
        results = instance.next(results)
        tracks.extend(results['items'])

    # only care about the ones with a url
    for track in tracks:
        if track['preview_url'] is not None:

            # print "\t", track

            name = track['name'].encode("utf-8")
            if name == q_track:

                # print "\t", track['name'].encode("utf-8")
                # print "\t", track['preview_url'].encode("utf-8")

                return track['preview_url'].encode("utf-8")

    return None


def get_artist_albums(q_artist, q_track):
    albums = []
    results = instance.artist_albums(q_artist['id'], album_type="album")

    # all artist albums
    albums.extend(results['items'])
    while results['next']:
        results = instance.next(results)
        albums.extend(results['items'])
    # print('Total albums:', len(albums))

    unique = set()  # skip duplicate albums
    for album in albums:
        name = album['name'].lower()
        if name not in unique:

            # print(name)

            unique.add(name)
            url = get_album_tracks(album, q_track)
            if url is not None:
                return url

    return None


# Main function that generate URLs
def generate_spotify_urls(input_filename, output_filename):
    data = dataset_processing.alternative_read_stored_data(input_filename)

    data_with_url = np.zeros((1, 4 + 2 * 25))
    for track in data:
        url = querySpotifyUrl(track)
        query = re.sub("[\(\[].*?[\)\]]", "", track[1] + " " + track[2])
        if url is None:
            artist = get_artist(track[1])
            song_name = track[2]
            if artist is not None:
                url = get_artist_albums(artist, song_name)
                if url is None:
                    print "ERROR\t'" + query + "' not found on Spotify."
        else:
            print query, url

        if url is None:
            data_with_url = np.vstack((data_with_url, np.hstack((np.insert(track, 3, "NONE")))))
        else:
            data_with_url = np.vstack((data_with_url, np.hstack((np.insert(track, 3, url)))))

        dataset_processing.alternative_store_data_in_file(data_with_url[1:], output_filename)


# Spotify API credentials
client_credentials_manager = SpotifyClientCredentials(
    client_id="d31b8fce2ead4943b1408cf3ba6f98bb",
    client_secret="08d00abdbb2b4f39891db99880dc819a")
instance = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)
