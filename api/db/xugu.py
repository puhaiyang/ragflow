import logging

from peewee import Database
from playhouse.migrate import SchemaMigrator, operation
from playhouse.pool import PooledDatabase

import xgcondb


class XuguDatabase(Database):
    paramstyle = 'qmark'  # ? 占位符

    def _connect(self):
        params = dict(self.connect_params)  # 拷贝一份，避免副作用

        host = params.get("host")
        port = params.get("port", "5138")
        database = params.get("database") or params.get("name") or self.database
        user = params.get("user")
        password = params.get("password")
        charset = params.get("charset", "utf8")

        # 🔍 打印【值 + 类型】，password 打码
        logging.error(
            "[XUGU DEBUG] connect params:\n"
            f"  host     = {host!r} ({type(host)})\n"
            f"  port     = {port!r} ({type(port)})\n"
            f"  database = {database!r} ({type(database)})\n"
            f"  user     = {user!r} ({type(user)})\n"
            f"  password = {'***' if password else None} ({type(password)})\n"
            f"  charset  = {charset!r} ({type(charset)})\n"
        )

        try:
            conn = xgcondb.connect(
                host=str(host) if host is not None else None,
                port=str(port) if port is not None else None,
                database=str(database) if database is not None else None,
                user=str(user) if user is not None else None,
                password=str(password) if password is not None else None,
                charset=str(charset) if charset is not None else None,
            )
            logging.error("[XUGU DEBUG] connect success & hook established")
            return conn
        except Exception as e:
            logging.exception("[XUGU DEBUG] connect failed")
            raise

    def _close(self, conn):
        try:
            conn.close()
        except Exception:
            pass

    def get_tables(self, schema=None):
        """
        Peewee 用于 table_exists()
        """
        query = 'SELECT TABLE_NAME FROM USER_TABLES'
        cursor = self.execute_sql(query)
        return [table for table, in cursor.fetchall()]

class XuguMigrator(SchemaMigrator):
    """
    Xugu 专用 SchemaMigrator，用于 Peewee 的 migrate 功能
    """

    def _primary_key_columns(self, table_name):
        """
        获取表的主键字段
        """
        sql = f"""
              select b.define
                from user_tables a
                inner join user_constraints b on a.table_id = b.table_id
                where b.cons_type = 'P'
                and a.table_name = UPPER('{table_name}')
        """
        cursor = self.database.execute_sql(sql)

        logging.error("[XUGU DEBUG] _primary_key_columns")

        pk_columns = []
        for row in cursor.fetchall():
            # row[0] 可能的值: '"ID"' 或 '"COL1","COL2"'
            define_str = row[0]
            if define_str:
                # 1. 按逗号拆分字段
                # 2. 去除每个字段前后的空格及双引号
                # 3. 过滤掉空字符串（防止末尾有逗号的情况）
                cols = [c.strip().strip('"') for c in define_str.split(',') if c.strip()]
                pk_columns.extend(cols)

        return pk_columns

    @operation
    def rename_table(self, old_name, new_name):
        """
        Xugu 中重命名表
        """
        sql = f'ALTER TABLE {old_name} RENAME TO {new_name}'

        logging.error("[XUGU DEBUG] rename_table")

        return [self.make_context().literal(sql)]

    @operation
    def add_column(self, table_name, field):
        """
        添加列
        """
        ddl = f'ALTER TABLE {table_name} ADD COLUMN {field.column_definition()}'

        logging.error("[XUGU DEBUG] add_column")

        return [self.make_context().literal(ddl)]

    @operation
    def drop_column(self, table_name, field):
        """
        删除列
        """
        ddl = f'ALTER TABLE {table_name} DROP COLUMN {field.name}'

        logging.error("[XUGU DEBUG] drop_column")

        return [self.make_context().literal(ddl)]

    @operation
    def rename_column(self, table_name, old_name, new_name):
        """
        重命名列
        """
        ddl = f'ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}'

        logging.error("[XUGU DEBUG] rename_column")

        return [self.make_context().literal(ddl)]

    @operation
    def add_index(self, table_name, fields, unique=False):
        """
        添加索引（注意 Xugu 对索引长度限制）
        """
        idx_name = f"{table_name}_{'_'.join(fields)}_idx"
        cols = ', '.join(fields)
        ddl = f'CREATE {"UNIQUE " if unique else ""}INDEX {idx_name} ON {table_name} ({cols})'

        logging.error("[XUGU DEBUG] add_index")

        return [self.make_context().literal(ddl)]

    @operation
    def drop_index(self, table_name, idx_name):
        ddl = f'DROP INDEX {idx_name}'

        logging.error("[XUGU DEBUG] drop_index")

        return [self.make_context().literal(ddl)]

    @operation
    def set_search_path(self, schema_name):
        """
        Xugu 不支持 search_path
        """

        logging.error("[XUGU DEBUG] set_search_path")

        return []