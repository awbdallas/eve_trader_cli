#!/usr/bin/env python3

import requests
import queue
import threading
import time
from json import loads

def avg_market_history(input_items, region, system, days=30):
    """
    Purpose: Add market history information to the input_items dict
    Parameters:  input_items, region_id, and systemid

    Notes:

    This uses threading and a lot of the code comes straight from 
    https://www.tutorialspoint.com/python/python_multithreading.html

    due to my lack of expereince with threading I took most of it initally,
    but I need to fine tune some of it so I'll work in the future to implement that
    """

    # I haven't used threading that much before so I'm taking form this guide:
    
    urls = []

    for item in input_items.keys(): 
        endpoint = "https://crest-tq.eveonline.com"
        # TODO error checking
        item_url = endpoint + "/inventory/types/{}/".format(item)
        market = "/market/{}/history/".format(region)

        url = endpoint + market + "?type=" + item_url

        urls.append({
            'url' : url,
            'item' : item,
            'system' :system
        })

    request_data(urls)

    for url in urls:

        avg_price = 0
        avg_order_count = 0
        avg_sold = 0
        
        # Last x days
        for day in url['data']['items'][-days:]:
            avg_price += day['avgPrice']
            avg_order_count += day['orderCount']
            avg_sold += day['volume']
        
        input_items[url['item']][url['system']]['market_history'] = {
                'avg_price' : avg_price /days,
                'avg_order_count' : avg_order_count /days,
                'avg_sold' : avg_sold/days
        }

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


