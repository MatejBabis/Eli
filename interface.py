# Processes the request received
def processRequest(req, state):
    # Name of the action
    if req.get("result").get("action") == "test":
        res = checkLive(state)
        return res

    elif req.get("result").get("action") == "preferenceElicitation":
        # If some error occurred on the way, don't generate new tracks
        # if the last ones have not been rated yet
        if len(state.Xtrain) is not len(state.Ytrain):
            t1, t2 = state.trackPairs[-1]
            t1_dsc = "'" + t1[2] + "' by " + t1[1]
            t2_dsc = "'" + t2[2] + "' by " + t2[1]
            t1_url = state.spotify.querySpotifyUrl(t1)
            t2_url = state.spotify.querySpotifyUrl(t2)
            t1_info = (t1_dsc, t1_url)
            t2_info = (t2_dsc, t2_url)
        else:
            t1_info, t2_info = state.returnTrackInfo()

        return ({
            "speech": "Here are two song samples:",
            "displayText": "Here are two song samples:",
            "source": "projecteli",
            "data": [t1_info, t2_info]
        }, state)

    elif req.get("result").get("action") == "preferenceElicitation.rank":
        number = req.get("result").get("parameters").get("number")
        # in case the preference was said as an ordinal
        if number == "":
            number = req.get("result").get("parameters").get("ordinal")
        preference = int(number) - 1     # second song is indexed as 1, first as 0

        succesfullyStored = state.ratePair(preference)
        if succesfullyStored is True:
            return ({
                "speech": "Track " + str(number) + " stored as preferred.",
                "displayText": "Track " + str(number) + " stored as preferred.",
                "source": "projecteli"
            }, state)
        else:
            return ({
                "speech": "Please make a valid choice.",
                "displayText": "Please make a valid choice.",
                "source": "projecteli"
            }, state)

    elif req.get("result").get("action") == "preferenceElicitation.repeat":
        number = req.get("result").get("parameters").get("number")
        # in case the preference was said as an ordinal
        if number == "":
            number = req.get("result").get("parameters").get("ordinal")
        trackToReplay = int(number) - 1     # second song is indexed as 1, first as 0

        if trackToReplay is 0 or trackToReplay is 1:
            return ({
                "speech": "Replaying track number " + str(number) + ".",
                "displayText": "Replaying track number " + str(number) + ".",
                "source": "projecteli",
                "data": trackToReplay
            }, state)
        else:
            return ({
                "speech": "I don't know how to play this track.",
                "displayText": "I don't know how to play this track.",
                "source": "projecteli"
            }, state)

    else:
        return {}


# Just a sample one
def checkLive(state):
    # Return the JSON response
    return ({
        "speech": "We are live.",
        "displayText": "We are live.",
        "source": "projecteli"
    }, state)


# Creates the output string to be received by the user
def outputString(outputList):
    if outputList is None:
        return {}

    item = outputList[0]
    desc = "Playing \'" + item["track"] + "\' by " + item["artist"] + "..."

    return {
        "speech": desc,
        "displayText": desc,
        "source": "projecteli",
        "data": item["preview_url"]
    }
