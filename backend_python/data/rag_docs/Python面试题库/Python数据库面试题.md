# Python数据库面试题

## 题目1：Python数据库连接池

**问题：** 什么是数据库连接池？Python中如何实现？

**标准答案：**
1. 连接池概念：
   - 预创建一批数据库连接
   - 使用时从池中获取，用完归还
   - 避免频繁创建和关闭连接
2. 为什么需要：
   - 数据库连接创建开销大
   - 限制并发连接数
   - 提高性能
3. Python实现：
   - SQLAlchemy：QueuePool、NullPool
   - DBUtils：PooledDB、PersistentDB
   - FastAPI：asyncio实现异步连接池
4. 配置参数：
   - pool_size：连接池大小
   - max_overflow：最大溢出连接数
   - pool_timeout：获取连接超时
5. 示例：
   ```python
   from sqlalchemy import create_engine
   
   engine = create_engine(
       "mysql://user:pass@host/db",
       pool_size=5,
       max_overflow=10
   )
   ```

**评估要点：**
- 是否理解连接池的作用
- 是否知道如何配置连接池
- 是否了解连接池的工作原理

---

## 题目2：Python的ORM选择

**问题：** Python有哪些ORM？如何选择？

**标准答案：**
1. SQLAlchemy：
   - 最流行的Python ORM
   - 支持同步和异步
   - 灵活性高，可选择SQL表达式
2. Django ORM：
   - Django框架自带
   - 约定大于配置
   - 适合Django项目
3. Peewee：
   - 轻量级ORM
   - 简单易用
   - 适合小型项目
4. Tortoise ORM：
   - 异步ORM
   - 类似Django的API
   - 适合异步项目
5. 选择建议：
   - 大型项目：SQLAlchemy
   - Django项目：Django ORM
   - 小型项目：Peewee
   - 异步项目：Tortoise

**评估要点：**
- 是否了解主流Python ORM
- 是否能根据需求选择合适的ORM
- 是否知道各ORM的特点

---

## 题目3：Python数据库迁移

**问题：** Python项目如何进行数据库迁移？

**标准答案：**
1. Alembic（SQLAlchemy）：
   - 最流行的数据库迁移工具
   - 自动生成迁移脚本
   - 支持版本控制
2. Django Migrations：
   - Django自带
   - makemigrations生成迁移文件
   - migrate执行迁移
3. 迁移流程：
   - 修改Model定义
   - 生成迁移脚本
   - 审查和修改脚本
   - 执行迁移
4. 最佳实践：
   - 保持迁移脚本干净
   - 定期合并迁移
   - 测试迁移脚本
   - 备份数据库
5. 示例（Alembic）：
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "add users table"
   alembic upgrade head
   ```

**评估要点：**
- 是否了解数据库迁移工具
- 是否能执行数据库迁移
- 是否知道迁移的最佳实践

---

## 题目4：Python的数据库事务

**问题：** Python中如何管理数据库事务？

**标准答案：**
1. 事务特性（ACID）：
   - 原子性：操作要么全部成功，要么全部失败
   - 一致性：事务前后数据一致
   - 隔离性：并发事务互不干扰
   - 持久性：提交后数据永久保存
2. SQLAlchemy事务：
   - 自动事务：Session默认开启事务
   - commit()：提交事务
   - rollback()：回滚事务
3. Django事务：
   - atomic()：原子操作
   - 装饰器和上下文管理器
4. 示例：
   ```python
   # SQLAlchemy
   session = Session()
   try:
       session.add(user)
       session.commit()
   except:
       session.rollback()
       raise
   
   # Django
   from django.db import transaction
   
   @transaction.atomic
   def transfermoney(from_user, to_user, amount):
       from_user.balance -= amount
       to_user.balance += amount
   ```

**评估要点：**
- 是否理解事务的ACID特性
- 是否能使用ORM的事务管理
- 是否知道事务的使用场景

---

## 题目5：Python的Redis使用

**问题：** Redis在Python项目中有哪些应用场景？

**标准答案：**
1. 缓存：
   - 缓存数据库查询结果
   - 缓存页面片段
   - 减少数据库压力
2. 会话存储：
   - 分布式Session
   - 跨服务器共享会话
3. 消息队列：
   - 发布订阅模式
   - 简单队列
4. 分布式锁：
   - Redisson
   - 简单锁实现
5. Python客户端：
   - redis-py：同步客户端
   - aioredis：异步客户端
6. 示例：
   ```python
   import redis
   
   r = redis.Redis(host='localhost', port=6379, db=0)
   
   # 缓存
   r.set('user:1', json.dumps(user_dict), ex=3600)
   
   # 分布式锁
   lock = r.lock('my_lock', timeout=5)
   with lock:
       # 临界区代码
       pass
   ```

**评估要点：**
- 是否了解Redis的应用场景
- 是否能使用Python操作Redis
- 是否知道Redis的高级用法
