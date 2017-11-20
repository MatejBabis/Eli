# -*- coding: utf-8 -*-

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlencode                      # noqa
from urllib.request import urlopen                      # noqa

import json                                             # noqa
import os                                               # noqa

import spotipy                                          # noqa
from datetime import timedelta                          # noqa
from spotipy.oauth2 import SpotifyClientCredentials     # noqa

from flask import Flask                                 # noqa
from flask import request                               # noqa
from flask import make_response                         # noqa
from flask import render_template                       # noqa

# Flask app should start in global layout
app = Flask(__name__, static_url_path='')


@app.route('/')
# Front-end redirection
def index():
    return render_template("index.html")


@app.route('/<path:filename>')
# Return files from the "/static" folder
def serveFileFromRoot(filename):
    return app.send_static_file(filename)


@app.route('/webhook', methods=['POST'])
# The webhook
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)
    res = json.dumps(res, indent=4)

    print("Response:")
    print(res)

    # Converts the response to a real response object
    r = make_response(res)
    # Incoming request headers
    r.headers['Content-Type'] = 'application/json'
    return r


# Processes the request received
def processRequest(req):
    # Name of the action
    if req.get("result").get("action") == "yahooWeatherForecast":
        # Yahoo weather base url
        baseurl = "https://query.yahooapis.com/v1/public/yql?"

        # Get the YQL query
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}

        # Change the query into a URL
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        # Get the result for the query
        result = urlopen(yql_url).read()
        # Decode the raw result into JSON
        data = json.loads(result)

        # Get the result
        res = makeWebhookResult(data)
        return res

    elif req.get("result").get("action") == "spotifyTrackInformation":
        # TODO: REMOVE HARDCODING
        # API credentials
        client_credentials_manager = SpotifyClientCredentials(
            client_id="d31b8fce2ead4943b1408cf3ba6f98bb",
            client_secret="08d00abdbb2b4f39891db99880dc819a")
        sp = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)
        # Get the query to be searched
        spotify_query = makeSpotifyQuery(req)
        # Search Spotify
        rawResults = sp.search(q=spotify_query, limit=10)

        print(rawResults)
        # Get the results
        metadata = songMetadata(rawResults)
        res = outputString(metadata)
        return res

    else:
        return {}


def makeSpotifyQuery(req):
    # Get the parameter value from the JSON request
    result = req.get("result")
    parameters = result.get("parameters")

    print(result)
    print(parameters)

    artist = ""
    track = ""

    if parameters.get("spotify-artist") is not None:
        artist = parameters.get("spotify-artist")

    if parameters.get("spotify-track") is not None:
        track = parameters.get("spotify-track")

    # Search for artist and/or track
    if (parameters.get("spotify-artist") and
            parameters.get("spotify-track") is None):
        return None
    else:
        return artist + " " + track


# Creates the Yahoo Query Language query necessary for the response
def makeYqlQuery(req):
    # Get the parameter value from the JSON request
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")

    if city is None:
        return None

    # YQL query
    return "select * from weather.forecast where woeid in (" + \
        "select woeid from geo.places(1) where text='" + city + "')"


# Creates the response that will be sent to the user
def makeWebhookResult(data):
    # Check if the response contains the expected data
    query = data.get('query')
    if query is None:
        return {}
    result = query.get('results')
    if result is None:
        return {}
    channel = result.get('channel')
    if channel is None:
        return {}

    # Collect the output variables
    condition = channel.get('item').get('condition')
    city = channel.get('location').get('city')
    units = channel.get('units').get('temperature')
    if (condition is None) or (city is None) or (units is None):
        return {}

    # Output sentence
    speech = "Today in " + city + ": " + condition.get('text') + \
        ", the temperature is " + condition.get('temp') + "°" + units

    # print("Output sentence:")
    # print(speech)

    # Return the JSON response
    return {
        "speech": speech,
        "displayText": speech,
        "source": "projecteli"
    }


# Transforms raw metadata into a dictionary form
def songMetadata(searchResults):
    if searchResults is None:
        return {}

    resultList = searchResults["tracks"]["items"]

    # For results sorted on song popularity
    # resultListBasedOnPopularity = sorted(resultList,
    #                                      key=lambda x: x['popularity'],
    #                                      reverse=True)
    # print resultListBasedOnPopularity

    topHit = resultList[0]

    # All artists
    artists = ""
    for a in topHit["artists"]:
        artists += a["name"] + ", "
    artists = artists[:-2]

    # Track duration (assuming < 1hr)
    lengthMs = topHit["duration_ms"]
    length = str(timedelta(milliseconds=lengthMs))
    # Remove the unnecessary hours and remaining milliseconds
    length = length[2:].split('.')[0]

    return {
        "track": topHit["name"],
        "artist": artists,
        "album": topHit["album"]["name"],
        "length": length
    }


# Creates the output string to be received by the user
def outputString(metadata):
    if metadata is None:
        return {}

    string = "Spotify search discovered this:" + \
             "\nTrack: " + metadata["track"] + \
             "\nArtist: " + metadata["artist"] + \
             "\nAlbum: " + metadata["album"] + \
             "\nLength: " + metadata["length"]

    # TODO: ARE ALL THE ENTRIES NECESSARY?
    return {
        "speech": string,
        "displayText": string,
        "source": "projecteli"
    }


if __name__ == '__main__':
    # Necessary for Heroku
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
