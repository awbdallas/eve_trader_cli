#!/usr/bin/env python3

import sys
import os
import MarketDB

from argparse import ArgumentParser


def main():

    parser = ArgumentParser()
    parser.add_argument('--system', help='System to query', default='30000142')
    parser.add_argument('--item', help='Item in question')
    args = parser.parse_args()


    if args.system and args.item:
        eveitem = MarketDB.EveItem()
        get_price_info(eveitem, args.item, args.system)
    else:
        print("Need System and Item")


def get_price_info(eveitem, item, system):
    print("Max Buy\tMin Sell\tAverage Sell\tAverage Amount\t")
    print("{0}\t{1}\t{2}\t{3}\t".format(
    eveitem.get_max_buy(item, system),
    eveitem.get_min_sell(item, system),
    eveitem.get_history_average_sell(item, system),
    eveitem.get_history_average_amount(item, system)
    )) 
    

if __name__ == '__main__':
    main()
