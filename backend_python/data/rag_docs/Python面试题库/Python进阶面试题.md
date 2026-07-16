# Python进阶面试题

## 题目1：Python的生成器和迭代器

**问题：** 请解释Python生成器和迭代器的区别。

**标准答案：**
1. 迭代器（Iterator）：
   - 实现__iter__和__next__方法
   - 可以被for循环遍历
   - 调用next()返回下一个元素
2. 生成器（Generator）：
   - 使用yield关键字的函数
   - 自动实现迭代器协议
   - 惰性求值，节省内存
3. 区别：
   - 生成器是迭代器的简化实现
   - 生成器使用yield，迭代器使用return
   - 生成器只能遍历一次
4. 使用场景：
   - 处理大数据集
   - 流式处理
   - 无限序列
5. 示例：
   ```python
   def count_up(n):
       i = 0
       while i < n:
           yield i
           i += 1
   
   for num in count_up(1000000):
       print(num)  # 不占用大量内存
   ```

**评估要点：**
- 是否理解迭代器协议
- 是否知道yield的工作原理
- 是否能手写生成器

---

## 题目2：Python的上下文管理器

**问题：** 什么是上下文管理器？如何实现？

**标准答案：**
1. 定义：管理资源的分配和释放
2. 协议：实现__enter__和__exit__方法
3. 使用：with语句
4. 实现方式：
   - 类实现：
     ```python
     class FileManager:
         def __init__(self, filename, mode):
             self.filename = filename
             self.mode = mode
         def __enter__(self):
             self.file = open(self.filename, self.mode)
             return self.file
         def __exit__(self, exc_type, exc_val, exc_tb):
             self.file.close()
     ```
   - 生成器实现：contextlib.contextmanager
5. 应用场景：文件操作、数据库连接、锁管理

**评估要点：**
- 是否理解上下文管理器的作用
- 是否能手写上下文管理器
- 是否知道contextlib的使用

---

## 题目3：Python的元类

**问题：** 什么是Python元类？有什么作用？

**标准答案：**
1. 定义：类的类，默认是type
2. 作用：控制类的创建行为
3. type()的双重用途：
   - 查看对象类型：type(obj)
   - 动态创建类：type(name, bases, dict)
4. 自定义元类：
   ```python
   class Meta(type):
       def __new__(cls, name, bases, attrs):
           # 修改类的创建过程
           return super().__new__(cls, name, bases, attrs)
   ```
5. 应用场景：
   - 框架设计（Django ORM）
   - 类型检查
   - 自动注册
   - AOP编程

**评估要点：**
- 是否理解type和元类的关系
- 是否能解释元类的应用场景
- 是否知道Django ORM中的元类应用

---

## 题目4：Python的异步编程

**问题：** Python的asyncio是如何工作的？

**标准答案：**
1. 协程（Coroutine）：
   - 使用async/await定义
   - 可以暂停和恢复执行
2. 事件循环（Event Loop）：
   - 调度和执行协程
   - 管理IO事件
3. 工作流程：
   - 定义协程函数
   - 创建事件循环
   - 将协程添加到事件循环
   - 运行事件循环
4. 示例：
   ```python
   import asyncio
   
   async def fetch_data():
       await asyncio.sleep(1)
       return "data"
   
   async def main():
       data = await fetch_data()
       print(data)
   
   asyncio.run(main())
   ```
5. 适用场景：IO密集型任务、网络编程

**评估要点：**
- 是否理解协程的概念
- 是否知道事件循环的作用
- 是否能编写异步代码

---

## 题目5：Python的设计模式

**问题：** 请举例说明Python中常用的设计模式。

**标准答案：**
1. 单例模式：
   ```python
   class Singleton:
       _instance = None
       def __new__(cls):
           if cls._instance is None:
               cls._instance = super().__new__(cls)
           return cls._instance
   ```
2. 工厂模式：
   - 根据参数创建不同类型的对象
   - 解耦对象创建和使用
3. 观察者模式：
   - 一对多依赖关系
   - 一个对象变化通知其他对象
4. 策略模式：
   - 定义算法族，可以互换
   - 避免多重条件判断
5. 装饰器模式：
   - Python内置支持
   - 动态添加功能

**评估要点：**
- 是否理解常用设计模式
- 是否能手写简单实现
- 是否知道在Python中的特殊实现
