#!/usr/bin/env python3

import requests
import json

def marketstat(items, location, **kwargs):
    """
    Purpose: Allow you to do a marketstat request to eve_central
    Parameters: list of items, and an id for region or system
    Returns: The data from market stat request in json form
    """
    # TODO support only getting certain fields. Could either do that
    # by deleting the others or something like that. 

    
    # limited by len of query. To just be lazy it's going to be set to 
    # 100 per query since that will more than likely be below the limit
    item_chunks = [items[x:x+100] for x in range(0, len(items), 100)]

    data = []

    # XML is supported by eve central, but I'm not supporting it
    endpoint = "http://api.eve-central.com/api/marketstat/json?"

    for item_chunk in item_chunks:

        url = endpoint 
        
        for item in item_chunk:
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

        for item in json.loads(response.text):
            data.append(item)

    return data
