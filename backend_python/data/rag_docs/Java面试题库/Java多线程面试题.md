# Java多线程面试题

## 题目1：synchronized和ReentrantLock的区别

**问题：** 请比较synchronized和ReentrantLock的区别。

**标准答案：**
1. 实现层面：synchronized是JVM层面，ReentrantLock是API层面
2. 锁释放：synchronized自动释放，ReentrantLock需手动unlock()
3. 可中断：synchronized不可中断，ReentrantLock可中断（lockInterruptibly()）
4. 公平性：synchronized非公平，ReentrantLock可选公平/非公平
5. 条件变量：ReentrantLock支持多个Condition，synchronized只有一个wait/notify
6. 性能：JDK6+后synchronized优化，性能差距不大

**评估要点：**
- 是否理解两者的设计层面差异
- 是否知道ReentrantLock的额外功能
- 是否了解性能演变

---

## 题目2：volatile关键字的作用

**问题：** volatile关键字有什么作用？为什么不保证原子性？

**标准答案：**
1. 作用：
   - 保证可见性：修改立即刷新到主内存
   - 保证有序性：禁止指令重排序
2. 不保证原子性的原因：
   - volatile只保证单次读/写的原子性
   - i++操作包含读、改、写三步，不是原子操作
3. 应用场景：
   - 状态标志
   - DCL单例模式
   - 一次性安全发布
4. 内存屏障实现：读操作前加LoadLoad屏障，写操作后加StoreStore屏障

**评估要点：**
- 是否理解可见性和有序性
- 是否知道i++的非原子性
- 是否了解实际应用场景

---

## 题目3：线程池的核心参数和执行流程

**问题：** 请说明线程池的核心参数和任务执行流程。

**标准答案：**
1. 核心参数：
   - corePoolSize：核心线程数
   - maximumPoolSize：最大线程数
   - keepAliveTime：空闲线程存活时间
   - workQueue：任务队列
   - threadFactory：线程工厂
   - handler：拒绝策略
2. 执行流程：
   - 当前线程数 < corePoolSize：创建核心线程执行
   - 当前线程数 >= corePoolSize：任务入队
   - 队列已满且当前线程数 < maximumPoolSize：创建非核心线程
   - 都不满足：执行拒绝策略
3. 拒绝策略：
   - AbortPolicy：抛出异常（默认）
   - CallerRunsPolicy：调用者执行
   - DiscardPolicy：静默丢弃
   - DiscardOldestPolicy：丢弃队列头部任务

**评估要点：**
- 是否理解执行流程
- 是否知道各参数的含义
- 是否了解拒绝策略的选择

---

## 题目4：ThreadLocal的原理和内存泄漏

**问题：** ThreadLocal是如何工作的？如何避免内存泄漏？

**标准答案：**
1. 原理：
   - 每个Thread维护一个ThreadLocalMap
   - ThreadLocal作为key，用户设置的值作为value
   - 不同线程操作各自的Map，互不影响
2. 内存泄漏风险：
   - ThreadLocalMap的Entry继承WeakReference
   - key是弱引用，可能被GC回收
   - value是强引用，不会被GC回收
   - 线程池场景下，线程不销毁，value无法回收
3. 避免方法：
   - 使用完毕后调用remove()方法
   - 线程池场景尤其重要

**评估要点：**
- 是否理解ThreadLocal的存储结构
- 是否知道弱引用的作用
- 是否了解内存泄漏的解决方案

---

## 题目5：死锁的条件和预防

**问题：** 什么是死锁？如何预防和避免？

**标准答案：**
1. 死锁定义：两个或多个线程互相持有对方需要的锁，导致永久阻塞
2. 产生条件（必须同时满足）：
   - 互斥条件：资源一次只能被一个线程持有
   - 占有并等待：持有资源的线程等待其他资源
   - 不可剥夺：已获取的资源不能被强制释放
   - 循环等待：线程之间形成资源等待环
3. 预防方法：
   - 破坏循环等待：按固定顺序获取锁
   - 设置超时时间：tryLock(timeout)
   - 使用银行家算法：资源分配前检查安全性
4. 检测和恢复：
   - 死锁检测算法
   - 资源剥夺或线程终止

**评估要点：**
- 是否理解四个必要条件
- 是否知道具体的预防方法
- 是否了解检测和恢复手段
