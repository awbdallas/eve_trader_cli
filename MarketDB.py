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
            self.conn = psycopg2.connect("dbname={0} user={1}".format(
                os.getenv('POSTGRES_DBNAME'),
                os.getenv('POSTGRES_USER')
            ))
        except:
            print("Unable to connect to DB")
            sys.exit(0)
        

class EveItem(MarketDB):

    def __init__(self):
        super().__init__()


    def get_all_market_items(self):
        cursor = self.conn.cursor() 

        cursor.execute(
           """\
            SELECT * FROM items WHERE market = 'True'
           """
        )

        rows = cursor.fetchall()

        list_of_itmes = [
            {
                'typeid' : row[0],
                'groupid' : row[1],
                'typename' : row[2],
                'volume' : row[3],
                'market' : row[4],

            } for row in rows]
