#!/usr/bin/env python3

import sys
import os
import MarketDB

from terminaltables import AsciiTable
from argparse import ArgumentParser


def main():

    parser = ArgumentParser()
    parser.add_argument('--system', help='System to query', default='30000142')
    parser.add_argument('--compare', help='Compare System Prices', nargs=2, default='30000142')
    parser.add_argument('--items', nargs ='+',  help='Item in question')
    parser.add_argument('--file', help='File of items')
    args = parser.parse_args()

    if args.compare:
        eveitem = MarketDB.EveItem()
        if args.items:
            items = check_item_input(eveitem, args.items)
        elif args.file:
            items = load_from_file(eveitem, args.file)
        else:
            print("Need items please")

        systems_info = []
        systems_info.append(get_price_info(eveitem, items, args.compare[0]))
        systems_info.append(get_price_info(eveitem, items, args.compare[1]))
        
        print_to_terminal(systems_info, mode=1)
    



    elif args.system:
        eveitem = MarketDB.EveItem()
        if args.items:
            items = check_item_input(eveitem, args.items)
        elif args.file:
            items = load_from_file(eveitem, args.file)
        else:
            print("Need items please")

        items_with_info = get_price_info(eveitem, items, args.system)
        print_to_terminal(items_with_info)
    else:
        print("Need System and Item")


def load_from_file(eveitem, input_file):
    """
    Purpose: Load input from file
    Parameters: MarketDB and input_file
    """
    holding = []
    try:
        with open(input_file, 'r') as fh:
            for line in fh:
                holding.append(line.strip())
    except:
        print("Error with reading file")

    return check_item_input(eveitem, holding)


def check_item_input(eveitem, items):
    """
    Purpose: Check all items to make sure they end up as typeids 
    Parameters: MarketDB and items argument
    """
    result_list = []
    
    for item in items:
        try:
            int(item)
            holding = item
        except ValueError:
            if "'" in item:

                holding = item.replace("'", "''")
            else:
                holding = item
            holding = eveitem.name_to_id(holding) 

            if not holding:
                print("{} is an invalid item".format(item))
                continue
        
        if eveitem.is_market_item(holding):
            result_list.append(holding)
        else:
            print("{} is an invalid item".format(item))
        

    return result_list

def print_to_terminal(items, mode=0):
    """
    Purpose: Print info to a terminal
    Parameters: items and a mode number
    """

    if mode == 0:
        table_data = [
                ['Name', 'Max Buy', 'Min Sell', 'Avg Sell', 'Avg Volume/Day']
        ]

        for item in items:
            table_data.append([
                item['name'], 
                convert_number(item['max_buy']), 
                convert_number(item['min_sell']), 
                convert_number(item['average_sell']), 
                convert_number(item['average_amount']), 
            ])

    if mode == 1:
        table_data = [
            ['Name', '1 Min Sell', '1 Avg Sell', '1 Volume', '2 Min Sell', '2 Avg Sell', '2 Volume']
        ]


        for x in range(len(items[0])):
            table_data.append([
                items[0][x]['name'], 
                convert_number(items[0][x]['min_sell']), 
                convert_number(items[0][x]['average_sell']), 
                convert_number(items[0][x]['average_amount']), 
                convert_number(items[1][x]['min_sell']), 
                convert_number(items[1][x]['average_sell']), 
                convert_number(items[1][x]['average_amount']), 
            ])

        
    table = AsciiTable(table_data)
    print(table.table)


def get_price_info(eveitem, items, system):
    """
    Purpose: Get price info in a form easy to manage 
    Parameters: MarketDB connection, list of items, system in question
    Returns: list of dicts with price info
    """
    
    result_list = []
    
    for item in items: 
        holding = {'item': item}
        holding['max_buy'] = eveitem.get_max_buy(item, system)
        holding['min_sell'] = eveitem.get_min_sell(item, system)
        holding['average_sell'] = eveitem.get_history_average_sell(item, system)
        holding['average_amount'] = float(eveitem.get_history_average_amount(item, system))
        holding['name'] = eveitem.id_to_name(item)

        result_list.append(holding)
    
    return result_list

def convert_number(input_number):
    try:
        # billions 
        if input_number / 1e9 > 1:
            return "%.2fB" % round((input_number / 1e9), 2)
        # millions
        elif input_number / 1e6 > 1:
            return "%.2fM" % round((input_number / 1e6), 2)
        # Thousands
        elif input_number / 1e3 > 1:
            return "%.2fK" % round((input_number / 1e3), 2)
        else:
            return "%.2f" % round(input_number, 2)
    except:
        return 0


if __name__ == '__main__':
    main()
