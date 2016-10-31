#!/usr/bin/env python3

import argparse

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
        items = load_tems()


"""
Purpose: Load all the items from the eve_items file into a dict
Returns: eve items in dict form. Keys can be either number or name
"""
def load_items():
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


def make_url(items, system):
    return None


def xml_to_dict():
    return None


if __name__ == '__main__':
    main()
