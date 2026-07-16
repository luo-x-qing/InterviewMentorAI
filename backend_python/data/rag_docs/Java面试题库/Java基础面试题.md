# Java基础面试题

## 题目1：HashMap和Hashtable的区别

**问题：** 请说明HashMap和Hashtable的主要区别。

**标准答案：**
1. 线程安全：HashMap线程不安全，Hashtable线程安全（方法级synchronized）
2. null键值：HashMap允许null键和null值，Hashtable不允许
3. 性能：HashMap性能更好，Hashtable性能较差
4. 继承关系：HashMap继承AbstractMap，Hashtable继承Dictionary
5. 推荐使用：多线程环境使用ConcurrentHashMap，而非Hashtable

**评估要点：**
- 能否准确说出线程安全差异
- 是否提到ConcurrentHashMap替代方案
- 是否了解底层实现差异

---

## 题目2：ArrayList和LinkedList的区别

**问题：** ArrayList和LinkedList有什么区别？各自适用什么场景？

**标准答案：**
1. 底层结构：ArrayList基于动态数组，LinkedList基于双向链表
2. 随机访问：ArrayList支持O(1)随机访问，LinkedList需要O(n)
3. 插入删除：ArrayList在中间位置插入删除需要移动元素O(n)，LinkedList为O(1)
4. 内存占用：LinkedList每个节点需要额外的前后指针空间
5. 适用场景：ArrayList适合频繁查询，LinkedList适合频繁插入删除

**评估要点：**
- 是否理解时间复杂度
- 是否能给出实际场景建议
- 是否提到内存占用差异

---

## 题目3：String、StringBuffer和StringBuilder的区别

**问题：** 请比较String、StringBuffer和StringBuilder的异同。

**标准答案：**
1. 可变性：String不可变，StringBuffer和StringBuilder可变
2. 线程安全：String是不可变的所以安全，StringBuffer线程安全，StringBuilder线程不安全
3. 性能：StringBuilder > StringBuffer > String（字符串拼接场景）
4. 使用场景：少量字符串操作用String，多线程大量操作用StringBuffer，单线程大量操作用StringBuilder

**评估要点：**
- 是否理解不可变性
- 是否了解性能差异
- 是否能根据场景选择

---

## 题目4：Java中的equals和==的区别

**问题：** 请解释equals和==的区别。

**标准答案：**
1. ==比较的是引用（内存地址），equals比较的是内容
2. 基本类型只能用==，比较值
3. 引用类型==比较是否指向同一对象，equals比较对象内容
4. String重写了equals方法，比较字符串内容
5. 自定义类需要重写equals才能比较内容

**评估要点：**
- 是否理解引用比较和内容比较
- 是否知道String的特殊性
- 是否了解如何重写equals

---

## 题目5：Java中的异常处理机制

**问题：** 请介绍Java的异常处理机制。

**标准答案：**
1. 异常体系：Throwable → Error / Exception
2. 受检异常：编译时检查，必须处理（try-catch或throws）
3. 非受检异常：RuntimeException，编译时不检查
4. try-catch-finally：finally块无论是否异常都会执行
5. try-with-resources：自动关闭资源（JDK7+）

**评估要点：**
- 是否理解异常体系结构
- 是否区分受检和非受检异常
- 是否了解try-with-resources
