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
        self.eve_system = EveSystem()


    def is_market_item(self, typeid):
        cursor = self.conn.cursor()
        cursor.execute(
        """
        SELECT market from items where typeid = {0}
        """.format(typeid)
        )

        try:
            return cursor.fetchone()[0]
        except TypeError:
            return False

    def id_to_name(self, typeid):
        cursor = self.conn.cursor() 
        cursor.execute(
        """
        SELECT typename from items where typeid = {}
        """.format(typeid)
        )

        return cursor.fetchone()[0]


    def name_to_id(self, typename):
        cursor = self.conn.cursor() 

        cursor.execute(
        """
        SELECT typeid from items where typename = '{}'
        """.format(typename)
        )

        try:
            return cursor.fetchone()[0]
        except TypeError:
            return None


    def get_item_information(self, typename):
        cursor = self.conn.cursor()

        cursor.execute(
        """
        SELECT typeid, groupid, typename, volume, market
        FROM items WHERE typename = '{}'
        """.format(typename)
        )
       
        row = cursor.fetchone()

        if row:
            return row
        else:
            return None


    def get_all_market_items(self):
        cursor = self.conn.cursor() 

        cursor.execute(
            """
            SELECT typeid, groupid, typename, volume, market
            FROM items WHERE market = 'True'
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

        return list_of_items


    def get_item_orders(self, item, system):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT issued, buy, price, volume FROM market_orders WHERE typeid = {} AND 
            stationid in {}
            """.format(
            (item, ', '.join(self.eve_system.system_to_station(system))))
        )

        rows = cursor.fetchall()

        list_of_items = [{
            'issued' : row[0],
            'buy' : row[1],
            'price' : row[2],
            'volume' : row[3]}
            for row in rows]

        return list_of_items


    def get_item_history(self, item, system):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT typeid, ordercount, lowprice, highprice, avgprice, volume 
            FROM market_data WHERE typeid = %s AND regionid = %s
            """, 
            (item, self.eve_system.system_to_region(system))
        )

        rows = cursor.fetchall()

        list_of_items_history = [{
            'typeid': row[0],
            'ordercount': row[1],
            'lowprice': row[2],
            'highprice': row[3],
            'avgprice': row[4],
            'volume': row[5],
            }
         for row in rows]

        return list_of_items_history


    def get_max_buy(self, item, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            SELECT MAX(price) from market_orders 
            WHERE buy = 'True' AND
            typeid = {0} AND
            stationid in ({1})
            """.format(
            item, ', '.join(str(station) for station in self.eve_system.system_to_station(system))
            )
        )
        return cursor.fetchone()[0]


    def get_min_sell(self, item, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            SELECT MIN(price) from market_orders 
            WHERE buy = 'False' AND stationid in ({0})
            AND typeid = {1}
            """.format(
            ', '.join(str(station) for station in self.eve_system.system_to_station(system)), item
            )
        )
        return cursor.fetchone()[0]

    
    def get_item_history(self, item, system):
        cursor = self.conn.cursor()
        cursor.execute(
        """
        SELECT avgprice, date, volume from market_data
        WHERE date > current_date - interval '30' day
        AND regionid = {}
        and typeid = {}
        ORDER BY date
        """.format(self.eve_system.system_to_region(system), item)
        )

        return cursor.fetchall()


    def get_history_average_sell(self, item, system, days=30):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            SELECT AVG(avgprice) from market_data 
            WHERE date > current_date - interval '%s' day
            AND regionid = %s
            AND typeid = %s
            """,
            (days, self.eve_system.system_to_region(system), item)
        )
        return cursor.fetchone()[0]
    

    def get_history_average_amount(self, item, system, days=30):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            SELECT AVG(volume) from market_data
            WHERE date > current_date - interval '%s' day
            AND regionid = %s
            AND typeid = %s
            """,
            (days, self.eve_system.system_to_region(system), item)
        )
        return cursor.fetchone()[0]


class EveSystem(MarketDB):

    def __init__(self):
        super().__init__()


    def system_to_station(self, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT stationid FROM stations where solarsystemid = {}
            """.format(system)
        )

        rows = cursor.fetchall()

        list_of_stations = [row[0] for row in rows]

        return list_of_stations


    def system_to_station_name(self, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT stationname, stationid FROM stations where solarsystemid = {}
            """.format(system)
        )

        rows = cursor.fetchall()

        if len(rows) == 0:
            return None
        else:
            return rows


    def check_system(self, system):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT stationid from stations where solarsystemid = {}
            """.format(system)
        )

        rows = cursor.fetchall()
        
        if len(rows) == 0:
            return False
        else:
            return True


    def region_to_system(self, region):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT * FROM stations where regionid = %s
            """, 
            (region)
        )

        rows = cursor.fetchall()
        
        list_of_stations = [
            {
                'stationid' : row[0],
                'regionid' : row[1],
                'solarsystemid' : row[2],
                'stationname' : row[3]

        } for row in rows]

        if len(rows) == 0:
            # There should at least be a system per region
            print("Invalid Region")

        return list_of_stations


    def system_to_region(self, system):
        cursor = self.conn.cursor()

        cursor.execute(
            """\
            SELECT regionid FROM stations where solarsystemid = {}
            """.format(
            system
            )
        )

        return cursor.fetchone()[0]
