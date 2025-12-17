import logging

from peewee import Entity
from playhouse.migrate import SchemaMigrator, operation
from playhouse.pool import PooledDatabase


class XuguMigrator(SchemaMigrator):
    """
    Xugu 专用 SchemaMigrator，用于 Peewee 的 migrate 功能
    """

    def _primary_key_columns(self, tbl):
        query = """
            select
                col_name
            from
                all_columns a
            left join all_constraints b on
                a.db_id = b.db_id
                and a.table_id = b.table_id
                and b.CONS_TYPE = 'P'
            where
                a.table_id = 
                                              (
                select
                    table_id
                from
                    all_tables
                where
                    table_name = '%s'
                limit 1)
                and b.define like '%' || a.col_name || '%'
            limit 1
        """
        cursor = self.database.execute_sql(query % tbl)
        return [row[0] for row in cursor.fetchall()]


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

    def _alter_table(self, ctx, table):
        return ctx.literal('ALTER TABLE ').sql(Entity(table))

    def _alter_column(self, ctx, table, column):
        return (self
                ._alter_table(ctx, table)
                .literal(' ALTER COLUMN ')
                .sql(Entity(column)))

    @operation
    def alter_column_type(self, table, column, field, cast=None):
        if cast is not None:
            raise ValueError('alter_column_type() does not support cast with '
                             'XUGU DB.')
        ctx = self.make_context()
        return (self
                ._alter_table(ctx, table)
                ._alter_column(column)
                .sql(field.ddl(ctx)))
