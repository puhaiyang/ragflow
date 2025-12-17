from xgpeewee import *

# 创建xugu peewee database
database = XuguDatabase(database='YSL', user='SYSDBA', password='SYSDBA', host='10.28.25.75', port=12345)


class User(Model):
    name = CharField()
    age = IntegerField()

    class Meta:
        database = database


database.create_tables([User])
user = User(name='John', age=25)
user.save()

# 更新用户的年龄
user = User.get(User.name == 'John')
user.age = 30
user.save()
print(user.id, user.name, user.age)

# 删除用户
user = User.get(User.name == 'John')
user.delete_instance()

# 批量插入

data = [
    {'name': 'Alice', 'age': 25},
    {'name': 'Bob', 'age': 30},
    {'name': 'Charlie', 'age': 35}
]

with database.atomic():  # 使用事务批量插入数据
    User.insert_many(data).execute()

# 查询所有用户
users = User.select()
for user in users:
    print(user.id, user.name, user.age)

User.delete().execute()
