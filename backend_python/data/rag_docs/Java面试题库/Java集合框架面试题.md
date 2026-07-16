# Java集合框架面试题

## 题目1：HashMap的底层实现原理

**问题：** 请详细说明HashMap的底层实现原理。

**标准答案：**
1. 数据结构：数组 + 链表 + 红黑树（JDK1.8+）
2. 默认参数：容量16，负载因子0.75，扩容阈值12
3. put流程：
   - 计算key的hash值（高16位异或低16位）
   - 通过hash & (capacity-1)定位桶
   - 桶为空直接插入，不为空则遍历链表/红黑树
   - 链表长度>=8且数组长度>=64时转红黑树
4. 扩容机制：容量翻倍，重新计算每个节点的位置
5. 线程不安全：多线程可能导致数据覆盖

**评估要点：**
- 是否理解hash扰动函数
- 是否知道链表转红黑树的条件
- 是否了解扩容过程

---

## 题目2：ConcurrentHashMap如何保证线程安全

**问题：** ConcurrentHashMap是如何实现线程安全的？

**标准答案：**
1. JDK1.7：分段锁（Segment），每个Segment是一个ReentrantLock
2. JDK1.8：CAS + synchronized，锁粒度细化到Node级别
3. put流程：
   - 计算hash定位Node
   - 如果Node为空，CAS插入
   - 如果Node不为空，synchronized锁住Node，遍历插入
4. size()：baseCount + CounterCell数组求和
5. 扩容：多线程协助迁移

**评估要点：**
- 是否了解JDK版本差异
- 是否理解CAS和synchronized的使用
- 是否知道锁粒度的优化

---

## 题目3：ArrayList的扩容机制

**问题：** ArrayList是如何扩容的？

**标准答案：**
1. 默认初始容量：10
2. 扩容时机：add元素时，如果size+1 > capacity
3. 扩容大小：新容量 = 旧容量 + 旧容量 >> 1（1.5倍）
4. 扩容过程：创建新数组，Arrays.copyOf复制元素
5. 性能影响：扩容涉及数组复制，应尽量预估容量

**评估要点：**
- 是否知道默认初始容量
- 是否理解扩容倍数
- 是否了解扩容的性能影响

---

## 题目4：LinkedList的实现原理

**问题：** LinkedList的底层数据结构是什么？有哪些特点？

**标准答案：**
1. 数据结构：双向链表
2. 节点结构：prev指针 + element + next指针
3. 特点：
   - 实现了List和Deque接口
   - 随机访问O(n)，插入删除O(1)（已知位置）
   - 不支持随机访问，实现RandomAccess接口会警告
4. 内存：每个节点额外占用16字节（两个指针）
5. 适用场景：频繁在头尾插入删除

**评估要点：**
- 是否理解双向链表结构
- 是否知道与ArrayList的时间复杂度对比
- 是否了解内存开销

---

## 题目5：TreeMap和LinkedHashMap的特点

**问题：** TreeMap和LinkedHashMap各有什么特点？

**标准答案：**
1. TreeMap：
   - 基于红黑树实现
   - key有序（自然排序或自定义Comparator）
   - 不允许null key
   - 时间复杂度O(log n)
2. LinkedHashMap：
   - 继承HashMap
   - 维护双向链表，保持插入顺序或访问顺序
   - 可用于实现LRU缓存
   - 有序遍历

**评估要点：**
- 是否理解红黑树的有序性
- 是否知道LinkedHashMap的LRU应用
- 是否能对比不同Map的适用场景
