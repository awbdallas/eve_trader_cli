#!/usr/bin/env python3

import cmd
import sys
import os
import MarketDB

from terminaltables import AsciiTable
from argparse import ArgumentParser


def main():

    parser = ArgumentParser()
    parser.add_argument('--shell', help='Start a shell for marketdb', action='store_true', default=False)
    args = parser.parse_args()

    if args.shell:
        MarketShell().cmdloop()


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
                ['Name', 'Max Buy', 'Min Sell', 'Margin', 'Margin Percent',
                    'Avg Sell', 'Avg Volume/Day']
        ]

        for item in items:
            if item['min_sell'] and item['max_buy']:
                margin =  item['min_sell'] - item['max_buy']
            else:
                margin = 0

            if margin != 0:
                margin_percent = (margin / item['max_buy']) * 100
            else:
                margin_percent = 0

            table_data.append([
                item['name'], 
                convert_number(item['max_buy']), 
                convert_number(item['min_sell']), 
                convert_number(margin),
                convert_number(margin_percent),
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
        try:
            holding['average_amount'] = float(eveitem.get_history_average_amount(item, system))
        except:
            holding['average_amount'] = 0
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


class MarketShell(cmd.Cmd):
    intro = 'Shell for market information'
    eveitem = MarketDB.EveItem()
    prompt = '> '


    def do_item(self,args):
        'Do an item lookup: SYSTEM ITEM1 ITEM2 ITEM3 or file'
        args = args.split(' ')
        if len(args) >= 2:
            system = args[0]
            input_items = args[1:]
            if self.eveitem.eve_system.check_system(system):
                if len(input_items) == 1 and os.path.isfile(input_items[0]):
                    items = load_from_file(self.eveitem, input_items[0])
                else:
                    items = check_item_input(self.eveitem, input_items)
                if len(items) > 0:
                    items_with_info = get_price_info(self.eveitem, items, system)
                    print_to_terminal(items_with_info)
                else:
                    print("Invalid amount of items")
            else:
                print("Invalid System")
        else:
            print("Needs at least an item and system")

    
    def do_item_compare(self,args):
        'Do an item Compare: SYSTEM 1 SYSTEM2 ITEM1 ITEM2 ITEM3'
        args = args.split(' ')
        if len(args) >= 3:
            system1 = args[0]
            system2 = args[1]
            input_items = args[2:]
            if self.eveitem.eve_system.check_system(system1) and\
                    self.eveitem.eve_system.check_system(system2):
                items = check_item_input(self.eveitem, input_items)
                if len(items) > 0:
                    systems_info = []
                    systems_info.append(get_price_info(self.eveitem, items, system1))
                    systems_info.append(get_price_info(self.eveitem, items, system2))

                    print_to_terminal(systems_info, mode=1)
                else:
                    print("Invalid amount of items")
            else:
                print("Invalid System")
        else:
            print("Needs at least an item and system")


    def do_item_lookup(self, args):
        'Get the item info of soemthing: ITEM'
        if len(args) >= 0:
            result = self.eveitem.get_item_information(args)
            if result:
                table_data = [['TypeID', 'GroupID', 'TypeName', 'Volume', 'Market']]
                table_data.append(
                        [result[0], result[1], result[2], result[3], result[4]]
                )
                table = AsciiTable(table_data)
                print(table.table)
            else:
                print("Invalid Item")


    def do_station_lookup(self, args):
        'Lookup for station information: SYSTEMID'
        if len(args) >= 0:
            result = self.eveitem.eve_system.system_to_station_name(args)
            if result:
                table_data = [['Station Name', 'StationID']]
                for station in result:
                    table_data.append([station[0], station[1]])
                table = AsciiTable(table_data)
                print(table.table)
            else:
                print("No station in that system")
            

    def do_find_trades(self, args):
        'Find items to trade(this will take awhile): SYSTEMID MINIMUM_ISK_PER_ITEM'
        args = args.split(' ')
        TAX_PERCENT = 6

        if len(args) == 2:
            table_data = [
                    ['Name', 'Min Sell', 'Max Buy', 'Margin', 'Average Selling']
            ]
            amount_profit = int(args[1])
            items = [item['typeid'] for item in self.eveitem.get_all_market_items()]
            item_info = get_price_info(self.eveitem, items, args[0])

            for item in item_info:
                if item['max_buy'] and item['min_sell'] and item['average_sell']:
                    margin = (item['min_sell'] - item['max_buy']) -\
                            (item['max_buy'] * .02) -\
                            (item['min_sell'] * .04)
                else:
                    continue

                if margin >= amount_profit:
                    table_data.append([
                        item['name'],
                        convert_number(item['min_sell']),
                        convert_number(item['max_buy']),
                        convert_number(margin),
                        convert_number(item['average_amount'])
                    ])

            table = AsciiTable(table_data)
            print(table.table)
        else:
            print("Invalid amount of arguments")


    def do_bye(self, args):
        'We are done here'
        sys.exit(0)


if __name__ == '__main__':
    main()
