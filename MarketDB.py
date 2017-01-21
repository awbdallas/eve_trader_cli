#!/usr/bin/env python3

import os
import sys
import psycopg2


class MarketDB():


    def __init__(self):
        db_name = os.getenv('POSTGRES_DBNAME')
        user_name = os.getenv('POSTGRES_USER')

        if db_name == None or user_name == None:
            print('Environment variables: POSTGRES_DBNAME and POSTGRES_USER not set')
            sys.exit(0)

        try:
            self.conn = psycopg2.connect("host=localhost dbname={0} user={1} password={2}".format(
                os.getenv('POSTGRES_DBNAME'),
                os.getenv('POSTGRES_USER'),
                os.getenv('POSTGRES_PASSWORD'),
            ))
        except:
            print("Unable to connect to DB")
            sys.exit(0)
        

class EveItem(MarketDB):

    def __init__(self):
        super().__init__()
        this.eve_system = EveSystem()


    def get_all_market_items(self):
        cursor = self.conn.cursor() 

        cursor.execute(
           """\
            SELECT * FROM items WHERE market = 'True'
           """
        )

        rows = cursor.fetchall()

        list_of_items = [
            {
                'typeid' : row[0],
                'groupid' : row[1],
                'typename' : row[2],
                'volume' : row[3],
                'market' : row[4],

            } for row in rows]


    def get_item_orders(self, item, system):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT * FROM market_orders WHERE typeid = {0} AND 
            WHERE stationid in ({1})
            """.format(item,
                ', '.join(eve_system(system_to_station))
                )
        )

        rows = cursor.fetchall()

        list_of_items = [{
            'issued' : row[1],
            'buy' : row[2],
            'price' : row[3],
            'volume' : row[4]}
            for row in rows]

        return list_of_items


class EveSystem(MarketDB):

    def __init__(self):
        super().__init()


    def system_to_station(self, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            SELECT * FROM stations where systemid = {0}
            """.format(system)
        )

        rows = cursor.fetchall()

        list_of_stations = [
            {
                'stationid' : row[0],
                'regionid' : row[1],
                'solarsystemid' : row[2],
                'stationname' : row[3]

            } for row in rows]

        return list_of_stations


    def region_to_system(self, region):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT * FROM stations where regionid = {0}
            """
        )

        rows = cursor.fetchall()
        
        list_of_stations = [
            {
                'stationid' : row[0],
                'regionid' : row[1],
                'solarsystemid' : row[2],
                'stationname' : row[3]

        } for row in rows]

        return list_of_stations

