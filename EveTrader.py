#!/usr/bin/env python3

import sys
import os
import MarketDB

from argparse import ArgumentParser


def main():

    parser = ArgumentParser()
    parser.add_argument('--system', help='System to query', default='30000142')
    parser.add_argument('--item', help='Item in question', nargs='+',
                        action='append')
    args = parser.parse_args()

    holding = MarketDB.EveItem()
    holding.get_all_market_items()


if __name__ == '__main__':
    main()
