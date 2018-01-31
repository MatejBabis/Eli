import spotipy
from datetime import timedelta
from spotipy.oauth2 import SpotifyClientCredentials


def makeSpotifyQuery(req):
    # Get the parameter value from the JSON request
    result = req.get("result")
    parameters = result.get("parameters")

    if parameters.get("spotify-artist") is not None:
        artist = parameters.get("spotify-artist")

    if parameters.get("spotify-track") is not None:
        track = parameters.get("spotify-track")

    # Search for artist and/or track
    if ((parameters.get("spotify-artist") is None) and
            (parameters.get("spotify-track") is None)):
        return None
    else:
        if artist and track:
            return track + " " + artist
        if artist:
            return artist
        if track:
            return track


# Transforms raw metadata into a dictionary form
def songMetadata(searchResults):
    if searchResults is None:
        return {}

    resultList = searchResults["tracks"]["items"]

    # For results sorted on song popularity
    # resultListBasedOnPopularity = sorted(resultList,
    #                                      key=lambda x: x['popularity'],
    #                                      reverse=True)
    # print(json.dumps(resultListBasedOnPopularity, indent=4))

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


# TODO: REMOVE HARDCODING
# API credentials
client_credentials_manager = SpotifyClientCredentials(
    client_id="d31b8fce2ead4943b1408cf3ba6f98bb",
    client_secret="08d00abdbb2b4f39891db99880dc819a")
instance = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)

# spotify_query = song_artist + " " + song_title
# result = sp.search(q=spotify_query, limit=1)
