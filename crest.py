#!/usr/bin/env python3

import requests
import queue
import threading
import time

from settings import _STORE_DB
from eve_trader import system_to_region
from json import loads


def crest_request(request_type, system, list_of_items):
    """
    Purpose: Add market history information to the input_items dict
    Parameters:  input_items, region_id, and systemid

    Notes:

    This uses threading and a lot of the code comes straight from 
    https://www.tutorialspoint.com/python/python_multithreading.html

    due to my lack of expereince with threading I took most of it initally,
    but I need to fine tune some of it so I'll work in the future to implement that
    """

    # 0: item_id, 1: systemid, 2: regionid, 3: endpoint
    region = system_to_region(system)
    urls = []
    endpoint = "https://crest-tq.eveonline.com"
    # There's more actions, but I'm really on concerned about 

    actions = {
        'item' : '{3}/inventory/types/{0}/',
        'item_history' : '{3}/market/{2}/history/?type={3}/inventory/types/{0}/',
        'item_sell' : '{3}/market/{2}/orders/sell/?type={3}/inventory/types/{0}/',
        'item_buy' : '{3}/market/{2}/orders/buy/?type={3}/inventory/types/{0}/'
    }

    for item in list_of_items: 
        urls.append({
            'url' : actions[request_type].format(item, system, region, endpoint),
            'item' : item,
            'system' :system
        })

    request_data(urls)

    # Now contains data
    return urls


def request_data(urls):
    """
    Purpose:
    Parameters: Urls that contain url, item, ans system/region in question
    Returns: None, urls will be populated afer this though with a field called
    Data that will be able to parsed and such after this. The idea is for
    """

    exitFlag = 0

    def process_request(queue):
        """
        Purpose: request and load data from request to json, and put inside
        the urls in order to get the data required
        Parameters: queue is passed in order to pull from. 
        """

        while not exitFlag:
            queueLock.acquire()
            if not workQueue.empty():
                url = queue.get() 
                queueLock.release()

                response = requests.get(url['url'])
                url['data'] = loads(response.text)
            
            else:
                queueLock.release()
            time.sleep(1)

    class request_thread(threading.Thread):
        def __init__(self, threadID, name, queue):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.queue = queue

        
        def run(self):
            process_request(self.queue)
        


    threadList = ["Thread-1", "Thread-2", "Thread-3", "Thread-4"]
    queueLock = threading.Lock()
    workQueue = queue.Queue(len(urls))
    threads = []
    threadID = 1
    url = []

    for tName in threadList:
        thread = request_thread(threadID, tName, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    queueLock.acquire()
    for url in urls:
        workQueue.put(url)
    queueLock.release()

    while not workQueue.empty():
        pass

    exitFlag = 1

    for t in threads:
        t.join()


