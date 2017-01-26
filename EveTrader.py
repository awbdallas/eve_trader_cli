#!/usr/bin/env python3

import sys
import os
import MarketDB

from terminaltables import AsciiTable
from argparse import ArgumentParser


def main():

    parser = ArgumentParser()
    parser.add_argument('--system', help='System to query', default='30000142')
    parser.add_argument('--items', nargs ='+',  help='Item in question')
    args = parser.parse_args()

    if args.system and args.items:
        eveitem = MarketDB.EveItem()
        items = check_item_input(eveitem, args.items)
        items_with_info = get_price_info(eveitem, items, args.system)
        print_to_terminal(items_with_info)
    else:
        print("Need System and Item")


def check_item_input(eveitem, items):
    """
    Purpose: Check all items to make sure they end up as typeids 
    Parameters: MarketDB and items argument
    """
    result_list = []
    
    for item in items:
        holding = item
        if item.isalpha():
            holding = eveitem.name_to_id(item)
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


if __name__ == '__main__':
    main()
