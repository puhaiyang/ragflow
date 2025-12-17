from peewee import *
import xgcondb
import peewee


class XuguDatabase(Database):
    field_types = {
        'AUTO': 'INTEGER AUTO_INCREMENT',
        'BIGAUTO': 'BIGINT AUTO_INCREMENT',
        'BOOL': 'BOOL',
        'DECIMAL': 'NUMERIC',
        'DOUBLE': 'DOUBLE',
        'FLOAT': 'FLOAT',
        'UUID': 'VARCHAR(40)'
        }
    operations = {
        'LIKE': 'LIKE',
        'ILIKE': 'LIKE',
        'REGEXP': 'REGEXP BINARY',
        'IREGEXP': 'REGEXP',
        'XOR': 'XOR'}
    param = '?'
    quote = '``'

    compound_select_parentheses = 2
    for_update = True
    index_using_precedes_table = True
    limit_max = 2 ** 64 - 1
    safe_create_index = False
    safe_drop_index = False

    def init(self, database, **kwargs):
        params = {
            'charset': 'utf8'}
        params.update(kwargs)
        if 'password' in params :
            params['password'] = params.pop('password')
        super(XuguDatabase, self).init(database, **params)

    def _connect(self):
        if xgcondb is None:
            raise ImproperlyConfigured('xugu driver not import!')
        conn = xgcondb.connect(database=self.database, autocommit=True,
                             **self.connect_params)
        return conn

    def _set_server_version(self, conn):
        pass

    def last_insert_id(self, cursor, query_type=None):
        query = ('SELECT id FROM  ' + cursor.getInsertTable() + " where rowid = '" +  cursor.getResultRowid() + "';")
        cursor = self.execute_sql(query)
        return cursor.fetchone()[0]


    def is_connection_usable(self):
        if self._state.closed:
            return False

        conn = self._state.conn
        if hasattr(conn, 'ping'):
            args = (False,)
            try:
                conn.ping(*args)
            except Exception:
                return False
        return True

    def default_values_insert(self, ctx):
        return ctx.literal('() VALUES ()')

    def begin(self, isolation_level=None):
        if self.is_closed():
            self.connect()
        with peewee.__exception_wrapper__:
            curs = self.cursor()
            if isolation_level:
                curs.execute('SET TRANSACTION ISOLATION LEVEL %s' %
                             isolation_level)
            curs.execute('BEGIN')

    def get_tables(self, schema=None):
        query = ('SELECT table_name FROM all_tables '
                 'WHERE db_id = (select db_id from all_databases where db_name = DATABASE()) '
                 'ORDER BY table_name')
        cursor = self.execute_sql(query)
        return [table for table, in cursor.fetchall()]

    def get_views(self, schema=None):
        query = ('SELECT VIEW_NAME AS table_name,DEFINE AS view_definition FROM ALL_VIEWS '
                 'WHERE db_id = (select db_id from all_databases where db_name = DATABASE()) '
                 'ORDER BY VIEW_NAME')
        cursor = self.execute_sql(query)
        return [peewee.ViewMetadata(*row) for row in cursor.fetchall()]

    def get_indexes(self, table, schema=None):
        cursor = self.execute_sql('SHOW INDEX FROM `%s`' % table)
        unique = set()
        indexes = {}
        for row in cursor.fetchall():
            if not row[1]:
                unique.add(row[2])
            indexes.setdefault(row[2], [])
            indexes[row[2]].append(row[4])
        return [IndexMetadata(name, None, indexes[name], name in unique, table)
                for name in indexes]

    def get_columns(self, table, schema=None):
        sql = """
            select col_name  as column_name,DECODE (NOT_NULL, TRUE, 1, 0) as is_nullable,type_name as data_type, def_val as column_default
            from all_columns where db_id = (select db_id from all_databases where db_name = DATABASE()) 
            and table_id = (select table_id from all_tables where table_name = ? and db_id = (select db_id from all_databases where db_name = DATABASE()))
            ORDER BY col_no"""
        cursor = self.execute_sql(sql, (table,))
        pks = set(self.get_primary_keys(table))
        return [peewee.ColumnMetadata(name, dt, null == 'YES', name in pks, table, df)
                for name, null, dt, df in cursor.fetchall()]

    def get_primary_keys(self, table, schema=None):
        cursor = self.execute_sql("select col_name from all_columns a left join all_constraints b on a.db_id = b.db_id and a.table_id = b.table_id  and b.CONS_TYPE = 'P'  where a.table_id = "
                                  "(select table_id from all_tables where table_name = '" + table + "' limit 1) and b.define like '%'||a.col_name||'%' limit 1" )
        return [row[0] for row in cursor.fetchall()]

    def get_foreign_keys(self, table, schema=None):
        query = """
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
                AND table_schema = DATABASE()
                AND referenced_table_name IS NOT NULL
                AND referenced_column_name IS NOT NULL"""
        cursor = self.execute_sql(query, (table,))
        return [
            peewee.ForeignKeyMetadata(column, dest_table, dest_column, table)
            for column, dest_table, dest_column in cursor.fetchall()]

    def get_binary_type(self):
        return xgcondb.Binary

    def conflict_statement(self, on_conflict, query):
        return


    def extract_date(self, date_part, date_field):
        return peewee.fn.EXTRACT(NodeList((SQL(date_part), SQL('FROM'), date_field)))

    def truncate_date(self, date_part, date_field):
        return peewee.fn.DATE_TRUNC(date_part, date_field)

    def to_timestamp(self):
        return self.model._meta.database.to_timestamp(self)

    def from_timestamp(self, date_field):
        return peewee.fn.FROM_UNIXTIME(date_field)

    def random(self):
        return peewee.fn.random()

    def get_noop_select(self, ctx):
        return ctx.sql(Select().columns(SQL('0')).where(SQL('false')))
