# This file serves as an interface to the model.
# Based on the request, it calls appropriate methods
# and returns correctly formatted response

import logging
from sys import stdout
import time
from datetime import timedelta

import model

log = logging.getLogger("Eli.interface")
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)


# Processes the request received
def processRequest(req, state):
    # Name of the action
    action = req.get("result").get("action")

    # User wishes to end the conversation
    if action == "ending.ending-yes":
        log.info("CONVERSATION TERMINATED!")
        return ({
            "speech": "Conversation ended. See you soon!",
            "displayText": "Conversation ended. See you soon!",
            "source": "projecteli",
        }, model.Model())

    # User asks for recommendation
    elif action == "recommendation":
        # Recommendation!
        if len(state.trainPairs) == 0 and len(state.Xtrain) == len(state.Ytrain):
            if state.recommendationsReady is True:
                return ({
                    "speech": "Here are 10 songs I think you'll like:",
                    "displayText": "Here are 10 songs I think you'll like:",
                    "source": "projecteli",
                    "data": state.experimentRecommendations
                }, state)
            else:
                return ({
                    "speech": "Still working on it, try again in couple of seconds.",
                    "displayText": "Still working on it, try again in couple of seconds.",
                    "source": "projecteli"
                }, state)
        # Too soon
        else:
            return ({
                "speech": "First, I need to gather more data about your preferences.",
                "displayText": "First, I need to gather more data about your preferences.",
                "source": "projecteli"
            }, state)

    # we have finished but the query is not about recommendation
    elif state.recommendationsReady is True:
        log.info("Preference assessment ended.")
        return ({
            "speech": "Elicitation has now finished. Ask for a list of recommendations or reload the webpage.",
            "displayText": "Elicitation has now finished. Ask for a list of recommendations or reload the webpage.",
            "source": "projecteli"
        }, state)

    # Give the user two song pairs
    elif action == "preferenceElicitation":
        # If some error occurred on the way, don't generate new tracks
        # if the last ones have not been rated yet
        if len(state.Xtrain) is not len(state.Ytrain):
            pair = state.seenPairs[-1]

            t1_meta = pair[0]
            t2_meta = pair[2]
            t1_url = t1_meta[3]
            t2_url = t2_meta[3]

            t1_dsc = "'" + t1_meta[2] + "' by " + t1_meta[1]
            t2_dsc = "'" + t2_meta[2] + "' by " + t2_meta[1]

            t1_info = (t1_dsc, t1_url)
            t2_info = (t2_dsc, t2_url)
        else:
            t1_info, t2_info = state.return_track_info()

        return ({
            "speech": "Here are two song samples:",
            "displayText": "Here are two song samples:",
            "source": "projecteli",
            "data": [t1_info, t2_info]
        }, state)

    # Store ranking by the user
    elif action == "preferenceElicitation.rank":
        number = req.get("result").get("parameters").get("number")
        # in case the preference was said as an ordinal
        if number == "":
            number = req.get("result").get("parameters").get("ordinal")
            # in case this still wasn't picked up
            if number == "":
                number = req.get("result").get("resolvedQuery")
        preference = int(number) - 1     # second song is indexed as 1, first as 0

        succesfullyStored = state.rate_pair(preference)
        if succesfullyStored is True:

            # logging
            pair = state.seenPairs[-1]
            sign = ' > ' if preference == 0 else ' < '
            log.info("Preference assessment: " + pair[0][0] + sign + pair[2][0])

            timeTaken = time.time() - state.trackStartTime
            log.info("Time taken: %s", str(timedelta(seconds=timeTaken)))
            state.cumAssessmentTime += timeTaken

            # We are done
            if len(state.trainPairs) == 0 and len(state.Xtrain) == len(state.Ytrain):

                return ({
                    "speech": "Track " + str(number) + " stored as preferred. This was the last pair to compare. You can now ask for recommendations.",
                    "displayText": "Track " + str(number) + " stored as preferred. This was the last pair to compare. You can now ask for recommendations.",
                    "source": "projecteli"
                }, state)

            else:   # usual case
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

    # Replay a track
    elif action == "preferenceElicitation.repeat":
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

    # Not recognised
    else:
        log.warn("USER QUERY NOT RECOGNISED!")
        log.warn("Query: %s", req)
        return ({
            "speech": "I don't understand. Try a different query.",
            "displayText": "I don't understand. Try a different query.",
            "source": "projecteli"
        }, state)

