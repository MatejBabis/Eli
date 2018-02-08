import spotipy
from datetime import timedelta
from spotipy.oauth2 import SpotifyClientCredentials


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

    # TODO: USE 'query' TO CHECK IF OUTPUT ACTUALLY CONTAINS DESIRED SONG

    return output


# search for track's sample url
def querySpotifyUrl(track):
    sp = instance

    artist = track[1]
    song = track[2]

    # construct Spotify query
    spotify_query = artist + " " + song
    spotify_query_result = sp.search(q=spotify_query, limit=1)

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


# TODO: REMOVE HARDCODING
# API credentials
client_credentials_manager = SpotifyClientCredentials(
    client_id="d31b8fce2ead4943b1408cf3ba6f98bb",
    client_secret="08d00abdbb2b4f39891db99880dc819a")
instance = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)
