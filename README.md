# Eli bot

This is a level 4 project by Matej Babis.

Languages: Python, Javascript & HTML

Webhook: `https://projecteli.ngrok.io/`

* Spotify Client ID: `d31b8fce2ead4943b1408cf3ba6f98bb`
* Dialogflow Client ID: `723e3f6e567d4260b6b93b4ad40a8783`


### Requirements:
* [ngrok](https://www.ngrok.com)
   * Dialogflow API requires a webhook to be connected to. By running a Flask Python app on localhost, we can tunnel the domain onto a local machine. Running the model locally is essential because of the size of the dataset.

### Execute by:
```
> python app.py
> ./ngrok http -subdomain=projecteli 5000

```

### Front End
Python web application made possible using Flask framework.

##### Libraries
* jQuery
* Dialogflow
* Google Analytics
* Normalize.css
* plyr

##### Back End
Collection of Python methods and libraries that build a model and query Million Song Dataset.

##### Libraries
* Million Song Dataset
* GPy
* NumPy
* VLC
* Spotify
