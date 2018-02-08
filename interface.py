# Processes the request received
def processRequest(req, state):
    # Name of the action
    if req.get("result").get("action") == "test":
        res = checkLive(state)
        return res

    elif req.get("result").get("action") == "preferenceElicitation":
        t1_info, t2_info = state.returnTrackInfo()
        return ({
            "speech": "Here are two song samples:",
            "displayText": "Here are two song samples:",
            "source": "projecteli",
            "data": [t1_info, t2_info]
        }, state)

    elif req.get("result").get("action") == "preferenceElicitation.rank":
        number = req.get("result").get("contexts")[0].get("parameters").get("number")
        # in case the preference was said as an ordinal
        if number == "":
            number = req.get("result").get("contexts")[0].get("parameters").get("ordinal")
        preference = int(number) - 1     # second song is indexed as 1, first as 0

        succesfullyStored = state.ratePair(preference)
        if succesfullyStored is True:
            return ({
                "speech": "Track " + number + " stored as preferred.",
                "displayText": "Track " + number + " stored as preferred.",
                "source": "projecteli"
            }, state)
        else:
            return ({
                "speech": "You fucked it. Try again.",
                "displayText": "You fucked it. Try again.",
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
