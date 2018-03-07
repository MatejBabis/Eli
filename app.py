# -*- coding: utf-8 -*-

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import json
import os
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler
from sys import stdout
from time import strftime
import time
from datetime import timedelta

import model
import interface

from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
from flask import current_app
from flask import send_from_directory

# Flask app should start in global layout
app = Flask("Eli", static_url_path='')

log = logging.getLogger("Eli")
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)


@app.route('/')
# Front-end redirection
def index():
    # model instantiation
    current_app.model = model.Model()
    return render_template("index.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')


@app.route('/blank')
def showSignUp():
    return render_template("blank.html")


@app.route('/webhook', methods=['POST'])
# The webhook
def webhook():
    req = request.get_json(silent=True, force=True)

    # print("\nRequest:")
    # print(json.dumps(req, indent=4) + "\n")

    compoundRes = interface.processRequest(req, current_app.model)
    res = json.dumps(compoundRes[0], indent=4)
    current_app.model = compoundRes[1]

    # print("\nResponse:")
    # print(res + "\n")

    # if we have complete data, build a model
    if len(current_app.model.trainPairs) == 0 \
            and len(current_app.model.Xtrain) == len(current_app.model.Ytrain) \
            and current_app.model.elicitationFinished is False:

        current_app.model.elicitationFinished = True
        log.info("\nLENGTH OF THE ELICITATION PROCESS: %s",
                 str(timedelta(seconds=(time.time() - current_app.model.elicitationStartTime))))
        log.info("AVERAGE DURATION OF PAIR ASSESSMENT: %s\n",
                 str(timedelta(seconds=(current_app.model.cumAssessmentTime / len(current_app.model.seenPairs)))))
        Thread(target=current_app.model.recommendation).start()

    # Converts the response to a real response object
    r = make_response(res)
    # Incoming request headers
    r.headers['Content-Type'] = 'application/json'
    return r


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    handler = RotatingFileHandler('logs/' + strftime('log_%H_%M_%d_%m_%Y.log'),
                                  maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(debug=True, port=port, host='0.0.0.0')
