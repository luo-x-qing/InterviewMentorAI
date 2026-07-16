# Python基础面试题

## 题目1：Python列表和元组的区别

**问题：** 请比较Python列表和元组的区别。

**标准答案：**
1. 可变性：
   - 列表（list）：可变，可以修改元素
   - 元组（tuple）：不可变，创建后不能修改
2. 语法：
   - 列表：使用方括号 []
   - 元组：使用圆括号 ()，单元素元组需要逗号 (1,)
3. 性能：
   - 元组创建和访问比列表快
   - 元组可以作为字典的key，列表不可以
4. 使用场景：
   - 列表：需要频繁修改的数据集合
   - 元组：固定不变的数据集合，如坐标、RGB颜色
5. 方法：
   - 列表：append、extend、pop、sort等
   - 元组：只有count和index

**评估要点：**
- 是否理解可变性差异
- 是否知道元组作为字典key的特性
- 是否能根据场景选择合适的数据结构

---

## 题目2：Python的深拷贝和浅拷贝

**问题：** 请解释Python深拷贝和浅拷贝的区别。

**标准答案：**
1. 浅拷贝（copy）：
   - 创建新对象，但内部元素仍是引用
   - copy()、列表切片[:]
   - 对嵌套对象的修改会影响原对象
2. 深拷贝（deepcopy）：
   - 创建新对象，内部元素也递归复制
   - copy.deepcopy()
   - 完全独立，修改不影响原对象
3. 示例：
   ```python
   import copy
   a = [[1, 2], [3, 4]]
   b = copy.copy(a)  # 浅拷贝
   c = copy.deepcopy(a)  # 深拷贝
   b[0][0] = 99  # a也会变
   c[0][0] = 99  # a不变
   ```

**评估要点：**
- 是否理解引用和复制的概念
- 是否能区分浅拷贝和深拷贝
- 是否知道如何选择拷贝方式

---

## 题目3：Python的装饰器

**问题：** 什么是Python装饰器？请举例说明。

**标准答案：**
1. 定义：装饰器是一个函数，接受函数作为参数，返回新函数
2. 作用：在不修改原函数的情况下扩展功能
3. 语法：@decorator
4. 示例：
   ```python
   def timer(func):
       import time
       def wrapper(*args, **kwargs):
           start = time.time()
           result = func(*args, **kwargs)
           print(f"耗时：{time.time()-start}秒")
           return result
       return wrapper
   
   @timer
   def slow_function():
       import time
       time.sleep(1)
   ```
5. 常用装饰器：@property、@staticmethod、@classmethod、@functools.wraps

**评估要点：**
- 是否理解装饰器的本质
- 是否能手写简单装饰器
- 是否知道functools.wraps的作用

---

## 题目4：Python的GIL是什么

**问题：** 什么是Python的GIL？它对多线程有什么影响？

**标准答案：**
1. GIL定义：全局解释器锁，确保同一时刻只有一个线程执行Python字节码
2. 存在原因：CPython的内存管理不是线程安全的
3. 影响：
   - CPU密集型任务：多线程无法利用多核
   - IO密集型任务：IO等待时会释放GIL，影响较小
4. 解决方案：
   - 使用多进程（multiprocessing）
   - 使用其他Python实现（Jython、PyPy）
   - 使用C扩展释放GIL
5. Python 3.12+：可选禁用GIL（PEP 703）

**评估要点：**
- 是否理解GIL的概念
- 是否知道GIL对不同类型任务的影响
- 是否了解解决方案

---

## 题目5：Python的内存管理

**问题：** Python是如何管理内存的？

**标准答案：**
1. 内存分配：
   - 私有堆：所有对象和数据结构
   - 内存管理器：pymalloc
2. 引用计数：
   - 主要机制：每个对象维护引用计数
   - 引用计数为0时回收
3. 垃圾回收：
   - 解决循环引用
   - 分代回收：0代、1代、2代
   - 标记-清除算法
4. 内存优化：
   - 小对象池：[-5, 256]的整数缓存
   - 字符串驻留（interning）
   - __slots__减少内存占用

**评估要点：**
- 是否理解引用计数机制
- 是否知道垃圾回收的作用
- 是否了解内存优化技巧
