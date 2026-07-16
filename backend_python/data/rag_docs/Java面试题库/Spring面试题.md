# Spring面试题

## 题目1：Spring IOC的原理

**问题：** 请解释Spring IOC的原理。

**标准答案：**
1. IOC概念：控制反转，将对象创建和依赖管理交给Spring容器
2. BeanFactory vs ApplicationContext：
   - BeanFactory：懒加载，基本功能
   - ApplicationContext：预加载，功能更丰富（事件、国际化等）
3. Bean生命周期：
   - 实例化 → 属性注入 → 初始化（@PostConstruct/InitializingBean）→ 使用 → 销毁
4. 循环依赖解决：
   - 三级缓存：singletonObjects、earlySingletonObjects、singletonFactories
   - 只能解决setter注入的循环依赖

**评估要点：**
- 是否理解IOC的核心思想
- 是否知道Bean的生命周期
- 是否了解循环依赖的解决方案

---

## 题目2：Spring AOP的原理

**问题：** Spring AOP是如何实现的？

**标准答案：**
1. AOP概念：面向切面编程，分离横切关注点
2. 核心概念：
   - 切面（Aspect）：横切关注点的模块化
   - 连接点（JoinPoint）：程序执行的特定点
   - 通知（Advice）：切面的具体行为
   - 切入点（Pointcut）：匹配连接点的表达式
3. 代理实现：
   - JDK动态代理：基于接口，Proxy.newProxyInstance
   - CGLIB代理：基于继承，生成子类
4. 选择规则：
   - 目标类实现了接口：JDK代理
   - 目标类没有实现接口：CGLIB
   - @EnableAspectJAutoProxy(proxyTargetClass=true)：强制CGLIB

**评估要点：**
- 是否理解AOP的核心概念
- 是否知道两种代理的区别
- 是否能解释代理选择规则

---

## 题目3：Spring Boot自动配置原理

**问题：** Spring Boot是如何实现自动配置的？

**标准答案：**
1. 核心注解：@SpringBootApplication
   - @EnableAutoConfiguration：启用自动配置
   - @ComponentScan：组件扫描
2. 自动配置流程：
   - @EnableAutoConfiguration导入AutoConfigurationImportSelector
   - 读取META-INF/spring.factories（或spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports）
   - 加载自动配置类
   - @Conditional条件注解决定是否生效
3. 常用条件注解：
   - @ConditionalOnClass：类路径存在
   - @ConditionalOnBean：容器存在Bean
   - @ConditionalOnProperty：配置属性存在
4. 自定义Starter：
   - 创建autoconfigure模块
   - 编写配置类和属性类
   - 注册到spring.factories

**评估要点：**
- 是否理解自动配置的流程
- 是否知道条件注解的作用
- 是否能自定义Starter

---

## 题目4：@Transactional的失效场景

**问题：** @Transactional在哪些场景下会失效？

**标准答案：**
1. 方法非public：Spring AOP只能代理public方法
2. 自我调用：同类方法内部调用，绕过了代理
3. 异常类型不对：默认只回滚RuntimeException和Error
4. 数据库不支持事务：如MyISAM引擎
5. 传播行为设置不当：如REQUIRES_NEW在新事务中
6. 异常被捕获：try-catch吞掉了异常
7. 没有被Spring管理：未注册为Bean

**评估要点：**
- 是否了解事务失效的常见场景
- 是否知道如何避免失效
- 是否理解Spring事务的底层实现

---

## 题目5：Spring Bean的作用域

**问题：** Spring Bean有哪些作用域？有什么区别？

**标准答案：**
1. singleton（默认）：
   - 整个IoC容器中只有一个实例
   - 每次注入都返回同一个对象
2. prototype：
   - 每次注入都创建新实例
   - 容器不管理完整生命周期
3. request（Web）：
   - 每个HTTP请求创建一个实例
   - 请求结束销毁
4. session（Web）：
   - 每个HTTP会话创建一个实例
   - 会话结束销毁
5. application（Web）：
   - 整个ServletContext生命周期内一个实例

**评估要点：**
- 是否理解各作用域的区别
- 是否知道作用域的使用场景
- 是否了解作用域对生命周期的影响
