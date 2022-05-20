import pymysql

class DBComs:
    def __init__(self, **kwargs):
        host = 'localhost' if 'host' not in kwargs else kwargs['host']
        user = 'pi' if 'user' not in kwargs else kwargs['user']
        pwd = '' if 'pwd' not in kwargs else kwargs['pwd']
        db = 'ovenDB' if 'dbName' not in kwargs else kwargs['dbName']

        self.com = pymysql.connect(
            host=host,
            user=user,
            password=pwd,
            database=db,
            cursorclass=pymysql.cursors.DictCursor
        ) or die('failed to connect')

        with self.com:
            self.cursor = self.com.cursor()

    def commit(self, table, colNames, data):
        colNames = ', '.join(colNames)
        data = ', '.join(data)
        command = 'INSERT INTO {} ({}) VALUES ({})'.format(table, colNames, data)
        print(command)
        self.cursor.execute(command)
        self.com.commit()

    def getRow(self, tableName, colNames='*'):
        if colNames != '*':
            colNames = '({})'.format(colNames)
        command = 'SELECT {} FROM {} ORDER BY id DESC LIMIT 1'.format(
            colNames,
            tableName
        )

        cursor = self.com.cursor()

        cursor.execute(command)
        rows = cursor.fetchone()

        return rows
