# -*- coding: utf-8 -*-

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import json
import os

import spotify

from flask import Flask
from flask import request
from flask import make_response
from flask import render_template

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

    # print("Request:")
    # print(json.dumps(req, indent=4))

    res = processRequest(req)
    res = json.dumps(res, indent=4)

    print("\nResponse:")
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
        # Get the result
        res = makeWebhookResult()
        return res

    elif req.get("result").get("action") == "spotifyTrackInformation":
        sp = spotify.instance

        print(sp)

        # Get the query to be searched
        # spotify_query = spotify.makeSpotifyQuery(req)
        spotify_query = "Robots Kraftwerk"
        # Search Spotify
        rawResults = sp.search(q=spotify_query, limit=10)

        print(rawResults)

        # Get the results
        metadata = spotify.songMetadata(rawResults)

        res = outputString(metadata)
        return res

    else:
        return {}

# Just a sample one
def makeWebhookResult():
    # Return the JSON response
    return {
        "speech": "We're live.",
        "displayText": "We're live.",
        "source": "projecteli"
    }


# Creates the output string to be received by the user
def outputString(outputList):
    if outputList is None:
        return {}

    string = "Spotify search discovered these songs:"
    for item in outputList:
        string += "\n\'" + item["track"] + "\' by " + item["artist"]

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
