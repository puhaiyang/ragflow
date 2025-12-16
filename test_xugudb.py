import xgcondb

# 创建数据库连接对象
conn = xgcondb.connect(host="10.28.25.75", port="12345", database="YSL", user="SYSDBA", password="SYSDBA",
                       charset='UTF8')
# 创建游标对象
cur = conn.cursor()
# 执行命令：创建一个新表
cur.execute("CREATE TABLE test_python (id integer identity PRIMARY KEY, name varchar, age integer);")

# 传递参数执行命令
cur.execute("INSERT INTO test_python (name, age) VALUES (?, ?)", ('test1', 18))

# 批量传递参数执行命令
cur.executemany("INSERT INTO test_python (name, age) VALUES (?, ?)", (('test2', 19), ('test3', 20), ('test4', 21)))

# 查询数据库获取数据
cur.execute("SELECT * FROM test_python;")
cur.fetchone()
cur.fetchmany(5)
