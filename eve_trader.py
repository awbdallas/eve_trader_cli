#!/usr/bin/env python3

import argparse
import json
import requests
import sys
from terminaltables import AsciiTable


def main():

    """
    TODO's for the program
    Get basic command for one item working for query
    Do it for large ones
    Create a "report" that will have things like shipping costs
    and things like that. Hopefully outputting to a spreadsheet of some sort
    """

    parser = argparse.ArgumentParser()
    # TODO multiple systems
    parser.add_argument("--system", help="System to query", default="30000142")
    parser.add_argument("--item", help="Item in question", nargs="+",
                        action="append")
    parser.add_argument("--file", help="File of items")
    args = parser.parse_args()

    # File or item is fine
    if args.system and args.item or args.system and args.file:
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

        eve_items = get_item_prices(input_items, eve_items, args.system)
        display_info(input_items, eve_items)
    else:
        print("Please have a system and item, or system and a file")


def display_info(input_items, eve_items):
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
        buy = eve_items[item]['market_info']['buy']['wavg']
        sell = eve_items[item]['market_info']['sell']['wavg']
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
    if input_number / 1e9 > 1:
        return "%.2fB" % round((input_number / 1e9), 2)

    # millions
    elif input_number / 1e6 > 1:
        return "%.2fM" % round((input_number / 1e6), 2)
    # thousands
    elif input_number / 1e3 > 1:
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


def get_item_prices(input_items, eve_items, system_id):
    urls = make_url(input_items, system_id)
    for url in urls:
        response = requests.post(url)
        response_list = json.loads(response.text)
       
        for item in response_list:
            current_item = str(item['buy']['forQuery']['types'][0])
            eve_items[current_item]['market_info'] = item

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


if __name__ == '__main__':
    main()
