# Project Eli

This is a level 4 project by Matej Babis.

Languages: Python, Javascript & HTML

Webhook: `https://projecteli.ngrok.io/`

* Spotify Client ID: `d31b8fce2ead4943b1408cf3ba6f98bb`
* Dialogflow Client ID: `723e3f6e567d4260b6b93b4ad40a8783`
* ngrok Pro token: `2jfkXCKdvDiqpTogmekeM_7GmFBngKeENs4BGcoCFU8`


### Requirements:
* [GPy](https://github.com/SheffieldML/GPy)
* [SciPy, NumPy, matplotlib](https://www.scipy.org/install.html)
* [Flask](http://flask.pocoo.org/)
* [ngrok](https://www.ngrok.com)
   * Dialogflow API requires a webhook to be connected to. By running a Flask Python app on localhost, we can tunnel the domain onto a local machine.
   * In order to simplify the installation process, a _Pro_ version of ngrok has been purchased.
      * Add the paid token: `./ngrok authtoken 2jfkXCKdvDiqpTogmekeM_7GmFBngKeENs4BGcoCFU8`.


After installing the dependencies, do the following
1. Add the following function to `{YOUR_PYTHON_ROOT}/Lib/site-packages/GPy/core/gp.py`:
```python
def predict_f(self, _Xnew, full_cov=False, kern=None):
   mu, var = self._raw_predict(_Xnew, full_cov=full_cov, kern=kern)
   return mu, var
```

2. Add the following line to `/Lib/site-packages/GPy/kern/__init__.py`:
```python
from .src.pjk import PjkRbf
```

3. Copy the `pjk.py` file into `/Lib/site-packages/GPy/kern/src/`.
   * This is the custom covariance function


### Execute by:
```
> python app.py
> ./ngrok http -subdomain=projecteli 5000
```
Now you can access [https://projecteli.ngrok.io/](https://projecteli.ngrok.io/).

### Bug list
* Sometimes no tracks are played after requesting a song pair.
   * Response is sent from the server, so possibly a Javascript issue.
   * __Mitigation__: Use the command again.
* Similarly, occasionally a preference judgment is not received in the same way.
   * __Mitigation__: Use the command again.
