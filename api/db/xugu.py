import logging
import time
import xgcondb

from peewee import Database
from playhouse.pool import PooledDatabase
from playhouse.migrate import SchemaMigrator, operation

class XuguDatabase(Database):
    paramstyle = 'qmark'  # ? 占位符

    # --- 新增：拦截并打印所有 SQL ---
    def execute_sql(self, sql, params=None, commit=True):
        # 1. 记录开始时间（可选，用于性能分析）
        start_time = time.time()

        # 2. 强行打印 SQL 和参数
        # 使用 logging.error 或 print 确保在 debug 级别不高时也能看到
        logging.error(f"\n[XUGU EXECUTE] SQL: {sql}")
        if params:
            logging.error(f"[XUGU EXECUTE] PARAMS: {params}")

        try:
            # 调用父类 (peewee.Database) 的原始执行逻辑
            res = super(XuguDatabase, self).execute_sql(sql, params, commit)
            return res
        except Exception as e:
            # 3. 如果执行失败，额外记录失败详情
            logging.error(f"[XUGU ERROR] Statement failed: {sql}")
            logging.error(f"[XUGU ERROR] Exception: {str(e)}")
            raise e

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
            # --- 核心拦截逻辑：Hook 这个 conn 实例的 cursor 方法 ---
            original_cursor_method = conn.cursor

            def hooked_cursor(*args, **kwargs):
                cursor = original_cursor_method(*args, **kwargs)
                original_execute = cursor.execute

                # 定义拦截 execute 的函数
                def hooked_execute(operation, parameters=None):
                    logging.error(f"\n>>> [FINAL_DRV_SQL]: {operation}")
                    if parameters:
                        logging.error(f">>> [FINAL_DRV_PARAMS]: {parameters}")
                    return original_execute(operation, parameters)

                # 将拦截后的函数绑定回当前的 cursor 实例
                cursor.execute = hooked_execute
                return cursor

            # 将包装后的 cursor 方法替换回 conn 实例
            conn.cursor = hooked_cursor

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
        return [self.make_context().literal(sql)]

    @operation
    def add_column(self, table_name, field):
        """
        添加列
        """
        ddl = f'ALTER TABLE {table_name} ADD COLUMN {field.column_definition()}'
        return [self.make_context().literal(ddl)]

    @operation
    def drop_column(self, table_name, field):
        """
        删除列
        """
        ddl = f'ALTER TABLE {table_name} DROP COLUMN {field.name}'
        return [self.make_context().literal(ddl)]

    @operation
    def rename_column(self, table_name, old_name, new_name):
        """
        重命名列
        """
        ddl = f'ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}'
        return [self.make_context().literal(ddl)]

    @operation
    def add_index(self, table_name, fields, unique=False):
        """
        添加索引（注意 Xugu 对索引长度限制）
        """
        idx_name = f"{table_name}_{'_'.join(fields)}_idx"
        cols = ', '.join(fields)
        ddl = f'CREATE {"UNIQUE " if unique else ""}INDEX {idx_name} ON {table_name} ({cols})'
        return [self.make_context().literal(ddl)]

    @operation
    def drop_index(self, table_name, idx_name):
        ddl = f'DROP INDEX {idx_name}'
        return [self.make_context().literal(ddl)]

    @operation
    def set_search_path(self, schema_name):
        """
        Xugu 不支持 search_path
        """
        return []