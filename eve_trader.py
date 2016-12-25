#!/usr/bin/env python3

import json
import os
import pyoo
import requests
import sys
import subprocess 
import time 
import crest
import evecentral

from argparse import ArgumentParser
from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, create_engine, 
        and_, Boolean, or_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from terminaltables import AsciiTable

Base = declarative_base()

_STORE_DB = "./data/eve.db"
_STORE_REPORTS = "./reports/"


def main():

    """
    TODO's for the program
    COMMENT this stuff properly. Oh god, it's awful.
    Fix the displaying into one control somehow 
    Fix items so that the ships packaged as far as volume 
    concerned
    Fix up main. It's doing too much I think.
    """

    if not os.path.exists(_STORE_DB):
        create_db()

    parser = ArgumentParser()
    parser.add_argument("--system", help="System to query", default="30000142")
    parser.add_argument("--sheet", help="Output to OO/LO spreadsheet", action='store_true',
            default=False)
    parser.add_argument("--item", help="Item in question", nargs="+",
                        action="append")
    parser.add_argument("--file", help="File of items")
    parser.add_argument("--shipping", help="System From, System too, Shipping Cost",
                        nargs="+", action="append")
    parser.add_argument("--directory", help="Directory for reports")
    args = parser.parse_args()

    if args.directory:
        _STORE_REPORTS = args.directory

    if args.file:
        input_items = load_user_input(file_input=args.file)
    else:
        input_items = load_user_input(list_input=args.item[0])

    # File or item is fine
    if (args.shipping and args.file) or (args.shipping and args.item):
        
        from_system = args.shipping[0][0]
        to_system = args.shipping[0][1]
        price = int(args.shipping[0][2])

        get_item_prices(input_items, [from_system, to_system])
        
        if args.sheet:
            display_shipping_sheet(input_items, [from_system, to_system], price)
        else:
            display_shipping_info(input_items, [from_system, to_system], price)

    elif (args.system and args.item) or (args.system and args.file):

        get_item_prices(input_items, [args.system])

        if args.sheet:
            display_market_sheet(input_items, args.system)
        else:
            display_market_info(input_items, args.system)
    else:
        print("Please have a system and item, or system and a file")


def get_price_info(input_items, system):
    """
    Purpose     : Populating input_items with price history information
    by calling eve central via the crest library
    Parameters  : input_items, system in question
    """

    region_id = system_to_region(system)
    crest.avg_market_history(input_items, region_id, system)


def system_to_region(system_id):
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()

    region = session.query(EveSystems).filter(EveSystems.systemID == system_id)\
            .all()[0].regionID

    session.close()

    return region

def create_db():
    """
    Purpose    : initialize db with Item model and solary system model
    Parameters : None
    """

    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    # items 
    with open('types.json') as item_file:
        data = json.load(item_file)
    
    add_list = []
    for item in data:
        add_list.append(EveItem(
                typeID = item['typeID'],
                volume = item['volume'],
                groupID = item['groupID'],
                market = item['market'],
                typeName = item['typeName']
        ))
    
    
    # CSV SystemID, RegionID, Region Name, System Name
    with open('solarsystem_ids.csv') as system_file:
        for line in system_file:
            line = line.strip()
            line = line.split(',')

            add_list.append(EveSystems(
                systemID = line[0],
                regionID = line[1],
                region = line[2],
                system = line[3]
                ))


    session.add_all(add_list)
    session.commit()
    session.close()


def display_shipping_info(input_items, systems, shipping_cost):
    """
    Purpose    : Displaying info in regards to shipping
    Parameters : input items that's populated, systems in question, and shipping
    Cost

    Note: Can't display all the information. Only basics just because 
    of limits in size because of it being terminal based
    """

    base_table = [['Item', 'From System Sell', 'To System Sell', 'Shipping Cost',
        'Difference (%)', 'Difference (isk)', 'To System Volume']]
    
    items = list(input_items.keys())
    items.sort() 

    for item in items:
        name = input_items[item]['typeName']
        sell_from = input_items[item][systems[0]]['market_info']['sell']['min']
        sell_to = input_items[item][systems[1]]['market_info']['sell']['min']
        shipping = float(input_items[item]['volume']) * shipping_cost
        difference_isk = (sell_to - sell_from) - shipping

        try:
            difference_percent = 100 * ((difference_isk) / sell_to)
        except ZeroDivisionError:
            difference_percent = "100"

        volume_to = input_items[item][systems[1]]['market_info']['sell']['volume']


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


def display_market_info(input_items, system):
    """
    Purpose    : Displaying the info to terminal to make it a little cleaner
    (It ended up looking like a spreadhseet...awkward)
    Parameters : input items which contains items populated with all the price
    information and shuch, and system in question
    """

    base_table = [['Item', 'Buy Max', 'Sell Min', 'Spread', 'Isk', 
        'Average Sell', 'Average Sold']]

    items = list(input_items.keys())
    items.sort()

    for item in items:
        name = input_items[item]['typeName']
        buy = input_items[item][system]['market_info']['buy']['wavg']
        sell = input_items[item][system]['market_info']['sell']['wavg']
        average_sell = input_items[item][system]['market_history']['avg_price']
        avg_sold = input_items[item][system]['market_history']['avg_sold']
        spread = 100 * ((sell - buy) / sell)
        spread_isk = (sell - buy)

        base_table.append([
            name,
            convert_number(buy),
            convert_number(sell),
            convert_number(spread) + '%',
            convert_number(spread_isk),
            convert_number(average_sell),
            convert_number(avg_sold)
        ])

    table = AsciiTable(base_table)
    print(table.table)


def convert_number(input_number):
    """
    Purpose    : Convert numbers to be easier to digest
    Returns    : Formatted number in str type to second decimal
    Parameters : Any number
    """

    try:
        # billions
        if input_number / 1e9 > 1 or input_number / 1e9 < -1:
            return "%.2fB" % round((input_number / 1e9), 2)
        # millions
        elif input_number / 1e6 > 1 or input_number / 1e6 < -1:
            return "%.2fM" % round((input_number / 1e6), 2)
        # thousands
        elif input_number / 1e3 > 1 or input_number / 1e3 < -1:
            return "%.2fK" % round((input_number / 1e3), 2)
        # hundreds
        else:
            return "%.2f" % round(input_number, 2)
        return "0"
    except:
        return "0"


def load_user_input(file_input=None, list_input=None):
    """
    Purpose    : Load user input into an easier way to deal with as well as
    Parameters : file_input (file_name) or list input ("list items") 
    Returns    : Dict of items with keys as type_ids
    """

    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    input_items = {}

    holding = []

    if file_input:
        with open(file_input, 'r') as user_file:
            for item in user_file:
                holding.append(item.strip())
    else:
        holding = list_input


    for item in holding:
        query_result = session.query(EveItem).filter(or_(EveItem.typeID == item,
            EveItem.typeName == item)).all()

        if len(query_result) == 0:
            print("Item: {} Does not exist".format(item))
        else:
            # typeid is unique, so should only be one
            holding_item = query_result[0]

            input_items[holding_item.typeID] = holding_item.to_dict()

    session.close()

    return input_items


def get_item_prices(input_items, system_ids):
    """
    Purpose    : get information from eve central  
    Parameters : input_items, system_ids
    Returns    : eve_items which will now be populated in format
    input_items[typeid][systemid]['market_info'] to get into the market_info
    """

    urls = []
    # Accounting for as many systems as allowed. 
    
    
    for system in system_ids:
        result = evecentral.marketstat(list(input_items.keys()), system)

        for item in result:
            current_item = item['buy']['forQuery']['types'][0]
            input_items[current_item][system] = {}
            input_items[current_item][system]['market_info'] = item

    for system in system_ids:
        get_price_info(input_items, system)


def display_shipping_sheet(input_items, systems, shipping_cost):
    """
    Purpose    : Turn info into a LibreOffice/Open OFfice spreadsheet
    Parameters : input items with market info, systems in question
    and the shipping cost 
    Returns    : None
    """

    subprocess.Popen(['mkfifo', 'temp'])
    p_office = subprocess.Popen(
        ' '.join(['/usr/bin/soffice', 
        '--accept="pipe,name=temp;urp;"',
        '--norestore', 
        '--nologo', 
        '--nodefault', 
        '--headless']),
        shell=True, stdout=subprocess.PIPE)

    # have to give it time to start 
    time.sleep(5)

    desktop = pyoo.Desktop(pipe='temp')

    doc = desktop.open_spreadsheet("./templates/shipping_template.ods")

    sheet = doc.sheets[0]

    headers = [
        'Item', 'From System Sell', 'To System Sell', 'Shipping Cost',
        'Difference (%)', 'To System Volume', 'Average Sold', 
        'Average Sold From', 'Average Sold To'
    ]
    sheet[0, :9].values = headers
    

    for row, item in enumerate(input_items.keys(), 1):

        sheet[row, :4].values = [
            input_items[item]['typeName'], # Name
            input_items[item][systems[0]]['market_info']['sell']['min'],
            input_items[item][systems[1]]['market_info']['sell']['min'], 
            float(input_items[item]['volume']) * shipping_cost
        ]

        sheet[row, 4].formula = '=($c{0} - ($b{0} + $d{0}))/ ($b{0} + $d{0})'.format(row + 1)

        sheet[row, 5:9].values = [
            input_items[item][systems[1]]['market_info']['sell']['volume'],
            input_items[item][systems[1]]['market_history']['avg_sold'],
            input_items[item][systems[0]]['market_history']['avg_price'],
            input_items[item][systems[1]]['market_history']['avg_price']
        ]


    dt = datetime.utcnow()
    doc.save('{1}shipping_report_{0:%Y}{0:%d}{0:%m}.ods'.format(dt, _STORE_REPORTS))
    doc.close()
    
    p_office.kill()
    subprocess.Popen(['rm', 'temp'])


def display_market_sheet(input_items, system):
    """
    Purpose    : Display info to spreadhseet for easier use 
    Parameters : Input items that contains all market info, and systems in 
    question
    """

    subprocess.Popen(['mkfifo', 'temp'])
    p_office = subprocess.Popen(
        ' '.join(['/usr/bin/soffice', 
        '--accept="pipe,name=temp;urp;"',
        '--norestore', 
        '--nologo', 
        '--nodefault', 
        '--headless']),
        shell=True, stdout=subprocess.PIPE)

    # have to give it time to start 
    time.sleep(5)

    desktop = pyoo.Desktop(pipe='temp')
    doc = desktop.open_spreadsheet("./templates/market_template.ods")
    sheet = doc.sheets[0]

    headers = ['Item', 'Buy Max', 'Sell Min', 'Spread', 'Isk Spread', 
        'Average Price', 'Average Sold']
    sheet[0, :7].values = headers
    

    for row,item in enumerate(input_items.keys(), 1):
        
        sheet[row, :3].values = [
            input_items[item]['typeName'], #name
            input_items[item][system]['market_info']['buy']['wavg'], #buy
            input_items[item][system]['market_info']['sell']['wavg'] #sell
        ]

        sheet[row, 3:5].formulas = [
            '=($C{0} - $B{0} )/ $B{0}'.format(row + 1),
            '=$C{0} - $B{0}'.format(row + 1)
        ]
        
        sheet[row, 5:7].values = [
            input_items[item][system]['market_history']['avg_price'],
            input_items[item][system]['market_history']['avg_sold']
        ]

    dt = datetime.utcnow()
    doc.save('{1}market_report_{0:%Y}{0:%d}{0:%m}.ods'.format(dt, _STORE_REPORTS))
    doc.close()
    
    p_office.kill()
    subprocess.Popen(['rm', 'temp'])


class Item(Base):
    """
    Purpose    : Defining the model for SQLAlchemy for Items.  
    """

    __tablename__ = 'market_data'
    id = Column(Integer, primary_key=True)
    typeID = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    system = Column(Integer)


class EveItem(Base):
    """
    Purpose: Defining model for the eve_items that exist in the universe, read
    in from types.json
    """

    __tablename__ = 'eve_items'
    typeID = Column(Integer, primary_key=True)
    volume = Column(Float)
    groupID = Column(Integer)
    market = Column(Boolean)
    typeName = Column(String(255))

    def to_dict(self):
        return {'typeID': self.typeID,
                'volume': self.volume,
                'groupID': self.groupID,
                'market': self.market,
                'typeName': self.typeName}

        
class EveSystems(Base):
    """
    Purpose: Defining model for the systems in eve
    """

    __tablename__ = 'eve_systems'
    systemID = Column(Integer, primary_key=True)
    regionID = Column(Integer)
    region = Column(String(255))
    system = Column(String(255))


if __name__ == '__main__':
    main()
