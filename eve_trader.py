#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import requests
import sys

from terminaltables import AsciiTable
from sqlalchemy import Column, Integer, String, DateTime, Float, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

_STORE_DB = "./previous_results.db"

def main():

    """
    TODO's for the program
    COMMENT this stuff properly. Oh god, it's awful.
    Get basic command for one item working for query
    Do it for large ones
    Create a "report" that will have things like shipping costs
    and things like that. Hopefully outputting to a spreadsheet of some sort
    """

    if not os.path.exists(_STORE_DB):
        create_db()

    parser = argparse.ArgumentParser()
    parser.add_argument("--system", help="System to query", default="30000142")
    parser.add_argument("--item", help="Item in question", nargs="+",
                        action="append")
    parser.add_argument("--file", help="File of items")
    parser.add_argument("--shipping", help="System From, System too, Shipping Cost",
                        nargs="+", action="append")
    args = parser.parse_args()

    # File or item is fine
    if (args.shipping and args.file) or (args.shipping and args.item):
        eve_items = load_eve_items()
        if args.file:
            input_items = load_user_items(args.file, eve_items)
        else:
            input_items = []

            for item in args.item[0]:
                if not eve_items.get(item, None):
                    print("Item {} is not a valid item".format(item))
                    sys.exit()
                else:
                    input_items.append(eve_items[item]['itemid'])
        from_system = args.shipping[0][0]
        to_system = args.shipping[0][1]
        price = int(args.shipping[0][2])

        eve_items = get_item_prices(input_items, eve_items, 
                [from_system, to_system])
        display_shipping_info(input_items, eve_items, 
                [from_system, to_system], price)
        store_shipping_info(input_items, eve_items, 
                [from_system, to_system])

    elif (args.system and args.item) or (args.system and args.file):
        eve_items = load_eve_items()

        if args.file:
            input_items = load_user_items(args.file, eve_items)
        else:
            input_items = []

            # TODO add support for systems
            # TODO convert for multiple items
            for item in args.item[0]:
                if not eve_items.get(item, None):
                    print("Item {} is not a valid item".format(item))
                    sys.exit()
                else:
                    input_items.append(eve_items[item]['itemid'])

        eve_items = get_item_prices(input_items, eve_items, [args.system])
        display_market_info(input_items, eve_items, args.system)
        store_market_info(input_items, eve_items, args.system)
    else:
        print("Please have a system and item, or system and a file")


def store_market_info(input_items, eve_items, system):
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()

    add_list = []

    for item in input_items:
        add_list.append(Item(system=system,
            price = eve_items[item][system]['market_info']['sell']['wavg']))
        
    session.add_all(add_list)
    session.commit()


# TODO maybe combine with **kwaargs and just check for systems
def store_shipping_info(input_items, eve_items, systems):
    
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()

    add_list = []

    for item in input_items:
        for system in systems:
            add_list.append(Item(system=system,
                price = eve_items[item][system]['market_info']['sell']['wavg']))
        
    session.add_all(add_list)
    session.commit()
    return None


def create_db():
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Base.metadata.create_all(engine)


def display_shipping_info(input_items, eve_items, systems, shipping_cost):
    base_table = [['Item', 'From System Sell', 'To System Sell', 'Shipping Cost',
        'Difference (%)', 'Difference (isk)', 'To System Volume']]

    for item in input_items:
        name = eve_items[item]['name']
        sell_from = eve_items[item][systems[0]]['market_info']['sell']['min']
        sell_to = eve_items[item][systems[1]]['market_info']['sell']['min']
        shipping = float(eve_items[item]['volume']) * shipping_cost
        difference_isk = (sell_to - sell_from) - shipping
        difference_percent = 100 * ((difference_isk) / sell_to)
        volume_to = eve_items[item][systems[1]]['market_info']['sell']['volume']


        base_table.append([
            name,
            convert_number(sell_from),
            convert_number(sell_to),
            convert_number(shipping),
            convert_number(difference_percent) + '%',
            convert_number(difference_isk),
            convert_number(volume_to)
            ])

    table = AsciiTable(base_table)
    print(table.table)

    return None


def display_market_info(input_items, eve_items, system):
    """
    Purpose: Displaying the info to terminal to make it a little cleaner
    Returns: None (default)
    TODO
    Need to have different modes. Like, station modes and shipping modes for
    region trading
    """

    base_table = [['Item', 'Buy Max', 'Sell Min', 'Spread', 'Isk']]
    for item in input_items:
        name = eve_items[item]['name']
        buy = eve_items[item][system]['market_info']['buy']['wavg']
        sell = eve_items[item][system]['market_info']['sell']['wavg']
        spread = 100 * ((sell - buy) / sell)
        spread_isk = (sell - buy)

        base_table.append([
            name,
            convert_number(buy),
            convert_number(sell),
            convert_number(spread) + '%',
            convert_number(spread_isk)
            ])

    table = AsciiTable(base_table)
    print(table.table)


def convert_number(input_number):
    """
    Purpose: convert numbers to be easier to digest
    Returns: Formatted double
    """

    # billions
    if input_number / 1e9 > 1 or input_number / 1e9 < -1:
        return "%.2fB" % round((input_number / 1e9), 2)

    # millions
    elif input_number / 1e6 > 1 or input_number / 1e6 < -1:
        return "%.2fM" % round((input_number / 1e6), 2)
    # thousands
    elif input_number / 1e3 > 1 or input_number / 1e3 < -1:
        return "%.2fK" % round((input_number / 1e3), 2)
    # everything that's left
    else:
        return "%.2f" % round(input_number, 2)

    return None


# TODO add checking in the future
def load_user_items(file_input, eve_items):
    user_items = []

    with open(file_input, 'r') as user_file:
        for line in user_file:
            line = line.strip()
            if eve_items.get(line, None):
                user_items.append(eve_items[line]['itemid'])

    return user_items


def load_eve_items():
    """
    Purpose: Load all the items from the eve_items file into a dict
    Returns: eve items in dict form. Keys can be either number or name
    """

    file_name = "./eve_items.csv"
    items = {}
    with open(file_name, 'r') as items_fh:
        for line in items_fh:
            # itemid, groupid, name, volume
            line = line.strip()
            line = line.split(',')
            items[line[0]] = {
                    'itemid': line[0],
                    'groupid': line[1],
                    'name': line[2],
                    'volume': line[3]
                    }
            items[line[2]] = {
                    'itemid': line[0],
                    'groupid': line[1],
                    'name': line[2],
                    'volume': line[3]
                    }
    return items


def get_item_prices(input_items, eve_items, system_ids):
    urls = []
    # Accounting for as many systems as allowed. 
    for system in system_ids:
        urls += make_url(input_items, system)

    for url in urls:
        response = requests.post(url)
        response_list = json.loads(response.text)
       
        for item in response_list:
            system = str(item['buy']['forQuery']['systems'][0])
            current_item = str(item['buy']['forQuery']['types'][0])
            eve_items[current_item][system] = {}
            eve_items[current_item][system]['market_info'] = item

    return eve_items


def make_url(items, system):
    """
    Purpose: Make the urls for the actual request
    Returns: A list of urls
    """

    base_url = "http://api.eve-central.com/api/marketstat/json?"
    urls = []

    # I believe the item limit is about 100 per request
    chunks = [items[i:i+100] for i in range(0, len(items), 100)]
    
    for chunk in chunks:
        urls.append(base_url + '&'.join('typeid=%s' % x for x in chunk)
                    + '&usesystem=%s' % system)
    return urls


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(Float)
    system = Column(Integer)


if __name__ == '__main__':
    main()


