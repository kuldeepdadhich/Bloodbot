from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import sys
import tweepy
import requests
import numpy as np

from keras.models import Sequential
from keras.layers import Dense
from textblob import TextBlob

import json
import os

from flask import Flask
from flask import request
from flask import make_response

consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
user = tweepy.API(auth)

# Where the csv file will live
FILE_NAME = 'historical.csv'

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
     result = req.get("result")
     parameters = result.get("parameters")
     quote=parameters.get("company").upper()
     if not get_historical(quote):
         return{}
    
    res=stock_prediction()
    print("Response:")
    print(res)
    return {
        "speech": res,
        "displayText": res,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }
    

    
def get_historical(quote):
    # Download our file from google finance
    url = 'http://www.google.com/finance/historical?q=NASDAQ%3A'+quote+'&output=csv'
    r = requests.get(url, stream=True)

    if r.status_code != 400:
        with open(FILE_NAME, 'wb') as f:
            for chunk in r:
                f.write(chunk)

        return True
        
 
        
def stock_prediction():

    # Collect data points from csv
    dataset = []

    with open(FILE_NAME) as f:
        for n, line in enumerate(f):
            if n != 0:
                dataset.append(float(line.split(',')[1]))

    dataset = np.array(dataset)

    # Create dataset matrix (X=t and Y=t+1)
    def create_dataset(dataset):
        dataX = [dataset[n+1] for n in range(len(dataset)-2)]
        return np.array(dataX), dataset[2:]
        
    trainX, trainY = create_dataset(dataset)

    # Create and fit Multilinear Perceptron model
    model = Sequential()
    model.add(Dense(8, input_dim=1, activation='relu'))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(trainX, trainY, nb_epoch=200, batch_size=2, verbose=2)

    # Our prediction for tomorrow
    prediction = model.predict(np.array([dataset[0]]))
    result = 'The price will move from %s to %s' % (dataset[0], prediction[0][0])

    return result
    

    
    
    
    


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
    
os.remove(FILE_NAME)    
