#!/usr/bin/env python3

import sys
import argparse
import requests

"""
"""
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--system", help="System to query")
    parser.add_argument("--item", help="Item in question")
    parser.add_argument("--file", help="File of items")
    args = parser.parse_args()

    # File or item is fine
    if args.system and args.item or args.system and args.file:
        eve_items = load_eve_items()

        if args.file:
            input_items = load_user_items(args.file, eve_items)
        else:
            input_items = args.item
            
            # TODO add support for systems
            # TODO convert for multiple items
            if not eve_items.get(args.item, None):
                print("Item {} is not a valid item".format(args.item))
                sys.exit() 
        
        get_item_prices(input_items, eve_items, args.system)


"""
Purpose: Load all the items from the eve_items file into a dict
Returns: eve items in dict form. Keys can be either number or name
"""
def load_eve_items():
    file_name = "./eve_items.csv"
    items = {}
    with open('filename', 'r') as items_fh:
        for line in items_fh:
            # itemid, groupid, name, volume
            line = line.split(',')
            items[line[0]] = {
                    'itemid': line[0],
                    'groupid': line[1],
                    'name': line[2],
                    'volume': line[3]
                    }
            items[line[1]] = {
                    'itemid': line[0],
                    'groupid': line[1],
                    'name': line[2],
                    'volume': line[3]
                    }
    return items


def get_item_prices(input_items, eve_items, system_id):
    return None


def make_url(items, system):
    base_url = "http://api.eve-central.com/api/marketstat?"
    # I believe the item limit is about 100 per request
    chunks = [items[i:i+100] for i in range(0, len(items), 100)]


    return None


def xml_to_dict():
    return None


if __name__ == '__main__':
    main()
