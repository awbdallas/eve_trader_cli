#!/usr/bin/env python3

import requests
from json import loads

def market_history(item, region, days=30):
    endpoint = "https://crest-tq.eveonline.com"
    # TODO error checking
    item = endpoint + "/inventory/types/{}/".format(item)
    market = "/market/{}/history/".format(region)

    url = endpoint + market + "?type=" + item

    response = requests.get(url)
    data = loads(response.text)
    
    return data['items'][-days:]
