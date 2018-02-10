# -*- coding: utf-8 -*-

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import json
import os

import model
import interface

from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
from flask import current_app

# Flask app should start in global layout
app = Flask(__name__, static_url_path='')

@app.route('/')
# Front-end redirection
def index():
    # model instantiation
    current_app.model = model.Interface()
    return render_template("index.html")

@app.route('/blank')
def showSignUp():
    return render_template("blank.html")

@app.route('/webhook', methods=['POST'])
# The webhook
def webhook():
    req = request.get_json(silent=True, force=True)

    print("\nRequest:")
    print(json.dumps(req, indent=4) + "\n")

    compoundRes = interface.processRequest(req, current_app.model)
    res = json.dumps(compoundRes[0], indent=4)
    current_app.model = compoundRes[1]

    print("\nResponse:")
    print(res + "\n")

    # Converts the response to a real response object
    r = make_response(res)
    # Incoming request headers
    r.headers['Content-Type'] = 'application/json'
    return r


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
