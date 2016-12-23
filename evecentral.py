#!/usr/bin/env python3

import requests
import json
import xml.etree.ElementTree as ET

def marketstat(items, location, **kwargs):
    # TODO support only getting certain fields. Could either do that
    # by deleting the others or something like that. 
    endpoint = "http://api.eve-central.com/api/marketstat"

    
    if kwargs.get('type', 'json') == 'json':
        url = endpoint + '/json?'
        del(kwargs['type'])
    else:
        url = endpoint 
    
    for item in items:
        url += 'typeid={}&'.format(item)

    for option,value in kwargs.items():
        url += '&{}={}'.format(option,value)

   # region
    if location[0] == '1':
        url += 'regionlimit={}'.format(location) 
   # system 
    else:
        url += 'usesystem={}'.format(location) 

    response = requests.post(url)

    return response.text
