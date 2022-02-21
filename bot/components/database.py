import psycopg2
from config.bot import DATABASE_URL
from bot.components.error import Error


class Database:
    cur = None

    def connect_to_db():
        global cur
        try:
            print('Connecting to database...')
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            conn.autocommit = True
            cur = conn.cursor()
            print('Successfully connected!')
        except Exception as e:
            Error.msg(e)

    def retrieve(tbl):
        try:
            cur.execute("SELECT post_id FROM " + tbl +
                        " WHERE post_id <> '' ORDER BY record_id DESC LIMIT 10")
            list = cur.fetchall()
            id_list = []
            for items in list:
                id_list.append(''.join(items))
            return id_list
        except (psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
            Error.msg(e)
            print('Attempting to reconnect now...')
            Database.connect_to_db()
        except (Exception, psycopg2.Error) as e:
            Error.msg(e)

    def insert(tbl, val):
        try:
            cur.execute("INSERT INTO " + tbl +
                        "(post_id) VALUES(%s)", (val,))
            print('[DB] Added id ' + val + ' to ' + tbl + '.')
        except (Exception, psycopg2.Error) as e:
            Error.msg(e)
            print('Attempting to reconnect now...')
            Database.connect_to_db()
            Database.insert(id, tbl, val)
