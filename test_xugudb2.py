#!/usr/bin/env python3

import os
import sys
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 打印Python搜索路径
logging.info(f"Python版本: {sys.version}")
logging.info(f"Python搜索路径: {sys.path}")

# 尝试安装psycopg2-binary
logging.info("正在尝试安装psycopg2-binary...")
os.system("pip install psycopg2-binary")


# 简单测试Xugu数据库连接，不依赖项目复杂结构
def test_xugu_simple():
    """简单测试Xugu数据库连接"""
    try:
        logging.info("正在测试Xugu数据库连接...")

        # 尝试直接使用psycopg2-binary
        try:
            import psycopg2
            logging.info("成功导入psycopg2模块！")
        except ImportError as e:
            logging.error(f"无法导入psycopg2模块: {e}")
            # 尝试安装并重新导入
            logging.info("正在尝试安装psycopg2-binary...")
            os.system("pip install psycopg2-binary")
            import psycopg2

        # Xugu数据库连接信息
        conn = psycopg2.connect(
            host='10.28.25.75',
            port=12345,
            user='SYSDBA',
            password='SYSDBA',
            dbname='YSL'
        )

        logging.info("成功连接到Xugu数据库！")

        # 测试执行SQL
        logging.info("正在测试执行SQL...")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        logging.info(f"SQL执行结果: {result}")

        # 测试创建表
        logging.info("正在测试创建表...")
        cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, name VARCHAR(50))")
        conn.commit()
        logging.info("成功创建表！")

        # 测试插入数据
        logging.info("正在测试插入数据...")
        cursor.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        conn.commit()
        logging.info("成功插入数据！")

        # 测试查询数据
        logging.info("正在测试查询数据...")
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchall()
        logging.info(f"查询结果: {result}")

        # 测试删除数据
        logging.info("正在测试删除数据...")
        cursor.execute("DELETE FROM test_table WHERE id = 1")
        conn.commit()
        logging.info("成功删除数据！")

        # 测试删除表
        logging.info("正在测试删除表...")
        cursor.execute("DROP TABLE test_table")
        conn.commit()
        logging.info("成功删除表！")

        # 关闭连接
        cursor.close()
        conn.close()
        logging.info("成功关闭数据库连接！")

        return True
    except Exception as e:
        logging.error(f"Xugu数据库连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_xugu_simple()
    if success:
        logging.info("Xugu数据库连接测试成功！")
        sys.exit(0)
    else:
        logging.error("Xugu数据库连接测试失败！")
        sys.exit(1)