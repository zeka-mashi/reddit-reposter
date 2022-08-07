import psycopg2
from bot.components.error import Error


class Database:
    def __init__(self, database_url):
        self.cur = None
        self.conn = None
        self.database_url = database_url

    def connect_to_db(self):
        try:
            print('Connecting to database...')
            self.conn = psycopg2.connect(self.database_url, sslmode='require')
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
            print('Successfully connected!')
        except Exception as e:
            Error.msg(e)

    def retrieve(self, tbl):
        try:
            self.cur.execute("SELECT post_id FROM " + tbl +
                             " WHERE post_id <> '' ORDER BY record_id DESC LIMIT 10")
            list = self.cur.fetchall()
            id_list = set()
            for items in list:
                id_list.add(''.join(items))
            return id_list
        except (psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
            Error.msg(e)
            print('Attempting to reconnect now...')
            self.connect_to_db()
        except (Exception, psycopg2.Error) as e:
            Error.msg(e)

    def insert(self, tbl, val):
        try:
            self.cur.execute("INSERT INTO " + tbl +
                             "(post_id) VALUES(%s)", (val,))
            print('[DB] Added id ' + val + ' to ' + tbl + '.')
        except (Exception, psycopg2.Error) as e:
            Error.msg(e)
            print('Attempting to reconnect now...')
            self.connect_to_db()
            self.insert(tbl, val)
