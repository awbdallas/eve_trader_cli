#!/usr/bin/env python3

import argparse
import json
import os
import pyoo
import requests
import sys

from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, create_engine, 
        and_, Boolean, or_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from terminaltables import AsciiTable

Base = declarative_base()

_STORE_DB = "./eve.db"
_STORE_REPORTS = "./"


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

    parser = argparse.ArgumentParser()
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
        store_shipping_info(input_items, [from_system, to_system])

        if args.sheet:
            display_shipping_sheet(input_items, [from_system, to_system], price)
        else:
            display_shipping_info(input_items, [from_system, to_system], price)

    elif (args.system and args.item) or (args.system and args.file):

        get_item_prices(input_items, [args.system])
        store_market_info(input_items, args.system)

        if args.sheet:
            display_market_sheet(input_items, args.system)
        else:
            display_market_info(input_items, args.system)
    else:
        print("Please have a system and item, or system and a file")


def store_market_info(input_items, system):
    """
    Purpose    : Store info in regards to markets
    Parameters : Input Typeids, eve_items dict, systems in question
    """
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()

    add_list = []

    for item in input_items.keys():
        add_list.append(Item(system=system,
            min_sell = input_items[item][system]['market_info']['sell']['wavg'],
            max_buy = input_items[item][system]['market_info']['buy']['wavg'],
            typeID = item))
        
    session.add_all(add_list)
    session.commit()


def store_shipping_info(input_items, systems):
    """
    Purpose    : Store info in regards to shipping from the query
    Parameters : Input Typeids, eve_items dict, systems in question
    """
    
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()

    add_list = []

    for item in input_items.keys():
        for system in systems:
            add_list.append(Item(system=system,
                min_sell = input_items[item][system]['market_info']['sell']['wavg'],
                max_buy = input_items[item][system]['market_info']['buy']['wavg'],
                typeID = item))
        
    session.add_all(add_list)
    session.commit()


def create_db():
    """
    Purpose    : initialize db with Item model
    """

    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    # stores it as a list with each item being a dict
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
    
    session.add_all(add_list)
    session.commit()
    


def display_shipping_info(input_items, systems, shipping_cost):
    """
    Purpose    : Displaying info in regards to shipping
    Parameters : typeids as input, eve_items that's populated with market data,
    and the system in question
    """

    base_table = [['Item', 'From System Sell', 'To System Sell', 'Shipping Cost',
        'Difference (%)', 'Difference (isk)', 'To System Volume']]

    for item in input_items.keys():
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
    Parameters : typeids as input, eve_items that's populated with market data,
    and the system in question
    """

    base_table = [['Item', 'Buy Max', 'Sell Min', 'Spread', 'Isk', 
        'Average Sell Min', 'Average Buy Max']]
    for item in input_items.keys():
        name = input_items[item]['typeName']
        buy = input_items[item][system]['market_info']['buy']['wavg']
        sell = input_items[item][system]['market_info']['sell']['wavg']
        spread = 100 * ((sell - buy) / sell)
        spread_isk = (sell - buy)
        average_sell = get_average_buy(item, system)
        average_buy = get_average_sell(item, system)

        base_table.append([
            name,
            convert_number(buy),
            convert_number(sell),
            convert_number(spread) + '%',
            convert_number(spread_isk),
            convert_number(average_sell),
            convert_number(average_buy)
        ])

    table = AsciiTable(base_table)
    print(table.table)


def get_average_buy(input_item, system):
    """
    Purpose    : Getting average buy
    Parameters : TypeID, and system in question
    Returns    : Average buy
    TODO: 
    Support Multiple Systems and multiple items
    """
    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    result = session.query(Item).filter(and_(Item.typeID == input_item, 
        Item.system == system)).all()
    
    buy_sum = 0

    for item in result:
        buy_sum += item.max_buy
    
    return buy_sum / len(result)


def get_average_sell(input_item, system):
    """
    Purpose    : Getting the average from the cached requested prices
    Parameters : TypeID, and system in question
    Returns    : average_sell
    Support Multiple Systems and multiple items
    """

    engine = create_engine('sqlite:///{}'.format(_STORE_DB))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    result = session.query(Item).filter(and_(Item.typeID == input_item, 
        Item.system == system)).all()
    
    sell_sum = 0

    for item in result:
        sell_sum += item.min_sell
    
    return sell_sum / len(result)


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
        # everything that's left
        else:
            return "%.2f" % round(input_number, 2)
        return "0"
    except:
        return "0"


def load_user_input(file_input=None, list_input=None):
    """
    Purpose    : Load user input into an easier way to deal with as well as
    Parameters : None
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

    return input_items


def get_item_prices(input_items, system_ids):
    """
    Purpose    : get information from eve central  
    Parameters : input_items
    Returns    : eve_items which will now be populated in format
    input_items[typeid][systemid]['market_info'] to get into the market_info
    """

    urls = []
    # Accounting for as many systems as allowed. 
    for system in system_ids:
        urls += make_url(list(input_items.keys()), system)



    for url in urls:
        response = requests.get(url)
        response_list = json.loads(response.text)
       
        for item in response_list:
            system = str(item['buy']['forQuery']['systems'][0])
            current_item = item['buy']['forQuery']['types'][0]
            input_items[current_item][system] = {}
            input_items[current_item][system]['market_info'] = item


def make_url(items, system):
    """
    Purpose    : Making URL with eve_central to query
    Parameters : the items to query, and the system to query
    Returns    : a list of urls
    """

    base_url = "http://api.eve-central.com/api/marketstat/json?"
    urls = []

    # I believe the item limit is about 100 per request
    chunks = [items[i:i+100] for i in range(0, len(items), 100)]
    
    for chunk in chunks:
        urls.append(base_url + '&'.join('typeid=%s' % x for x in chunk)
                    + '&usesystem=%s' % system)
    return urls


def display_shipping_sheet(input_items, systems, shipping_cost):
    """
    Purpose    : Turn info into a LibreOffice/Open OFfice spreadsheet
    Parameters : typeds as input, eve items with market data, systems in question
    and the shipping cost for it
    Returns    : None
    """

    desktop = pyoo.Desktop('localhost', 2002)

    doc = desktop.open_spreadsheet("./shipping_template.ods")

    sheet = doc.sheets[0]

    headers = [
        'Item', 'From System Sell', 'To System Sell', 'Shipping Cost',
        'Difference (%)', 'To System Volume', 'Average_Sell_From', 
        'Average_Sell_To'
    ]
    sheet[0, :8].values = headers
    

    for row, item in enumerate(input_items.keys(), 1):
        name = input_items[item]['typeName']
        sell_from = input_items[item][systems[0]]['market_info']['sell']['min']
        sell_to = input_items[item][systems[1]]['market_info']['sell']['min']
        shipping = float(input_items[item]['volume']) * shipping_cost
       
        average_sell_from = get_average_sell(item, systems[0])
        average_sell_to = get_average_sell(item, systems[1])

        volume_to = input_items[item][systems[1]]['market_info']['sell']['volume']

        sheet[row, :4].values = [
            name,
            sell_from,
            sell_to,
            shipping
        ]

        sheet[row, 4].formula = '=($c{0} - ($b{0} + $d{0}))/ $b{0}'.format(row + 1)

        sheet[row, 5:8].values = [
            volume_to,
            average_sell_from,
            average_sell_to
        ]


    dt = datetime.utcnow()
    doc.save('{1}shipping_report_{0:%Y}{0:%d}{0:%m}.ods'.format(dt, _STORE_REPORTS))
    doc.close()


def display_market_sheet(input_items, system):
    """
    Purpose    : Display info to spreadhseet for easier use 
    Parameters : typeids as input, eve_items that's populated with market data,
    and the system in question
    """

    desktop = pyoo.Desktop('localhost', 2002)

    doc = desktop.open_spreadsheet("./market_template.ods")


    sheet = doc.sheets[0]

    headers = ['Item', 'Buy Max', 'Sell Min', 'Spread', 'Isk Spread', 
        'Average Sell Min', 'Average Buy Max']
    sheet[0, :7].values = headers
    

    for row,item in enumerate(input_items.keys(), 1):
        average_sell = get_average_sell(item, system)
        average_buy = get_average_Buy(item, system)
        
        sheet[row, :3].values = [
            input_items[item]['typeName'], #name
            input_items[item][system]['market_info']['buy']['wavg'], #buy
            input_items[item][system]['market_info']['sell']['wavg'] #sell
        ]

        sheet[row, 3:5].formulas = [
            '=($C{0} - $B{0} )/ $B{0}'.format(row + 1),
            '=$C{0} - $B{0}'.format(row + 1)
        ]
        
        
        sheet[row, 5:6].values [
            average_sell,
            average_buy
        ]


    dt = datetime.utcnow()
    doc.save('{1}market_report_{0:%Y}{0:%d}{0:%m}.ods'.format(dt, _STORE_REPORTS))
    doc.close()


class Item(Base):
    """
    Purpose    : Defining the model for SQLAlchemy for Items.  
    """

    __tablename__ = 'market_data'
    id = Column(Integer, primary_key=True)
    typeID = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    min_sell = Column(Float)
    max_buy = Column(Float)
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


if __name__ == '__main__':
    main()
