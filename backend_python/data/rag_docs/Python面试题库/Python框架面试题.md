# Python框架面试题

## 题目1：Django的ORM原理

**问题：** Django ORM是如何工作的？

**标准答案：**
1. ORM概念：对象关系映射，将Python类映射到数据库表
2. 核心组件：
   - Model：定义数据结构
   - QuerySet：查询接口
   - Manager：管理器，提供查询方法
3. 工作流程：
   - 定义Model类
   - 通过makemigrations生成迁移文件
   - 通过migrate执行迁移
   - 使用Model.objects进行CRUD
4. 延迟加载：
   - QuerySet是懒加载的
   - 访问数据时才执行SQL
5. N+1问题：
   - select_related：JOIN查询
   - prefetch_related：预加载关联对象

**评估要点：**
- 是否理解ORM的基本原理
- 是否知道QuerySet的懒加载特性
- 是否了解N+1问题和解决方案

---

## 题目2：Flask和Django的区别

**问题：** Flask和Django有什么区别？各自适用什么场景？

**标准答案：**
1. Flask：
   - 轻量级框架，核心简单
   - 需要自己选择组件（数据库、表单等）
   - 适合小型项目和微服务
   - 灵活性高
2. Django：
   - 全功能框架，自带ORM、Admin、表单等
   - 约定大于配置
   - 适合中大型项目
   - 开发效率高
3. 技术差异：
   - 路由：Flask使用装饰器，Django使用URL配置
   - 模板：Flask使用Jinja2，Django使用自己的模板引擎
   - ORM：Flask使用SQLAlchemy，Django使用自己的ORM
4. 选择建议：
   - 小项目、微服务：Flask
   - 大项目、团队协作：Django

**评估要点：**
- 是否理解两者的设计哲学
- 是否能根据项目需求选择框架
- 是否了解各自的技术特点

---

## 题目3：FastAPI的性能优势

**问题：** FastAPI为什么性能高？与其他框架相比有什么优势？

**标准答案：**
1. 性能原因：
   - 基于ASGI，异步支持
   - 使用Pydantic进行数据验证
   - Starlette底层，基于uvicorn
2. 核心特性：
   - 异步支持：async/await
   - 自动生成API文档：OpenAPI
   - 类型提示驱动：依赖注入
3. 对比：
   - vs Flask：FastAPI原生异步，Flask需要额外库
   - vs Django：FastAPI更轻量，异步支持更好
4. 适用场景：
   - 高性能API服务
   - 实时应用（WebSocket）
   - 微服务架构
5. 示例：
   ```python
   from fastapi import FastAPI
   
   app = FastAPI()
   
   @app.get("/items/{item_id}")
   async def read_item(item_id: int):
       return {"item_id": item_id}
   ```

**评估要点：**
- 是否理解异步编程的优势
- 是否知道FastAPI的核心特性
- 是否能对比不同框架的适用场景

---

## 题目4：Python的依赖注入

**问题：** 什么是依赖注入？FastAPI是如何实现依赖注入的？

**标准答案：**
1. 依赖注入概念：
   - 对象的依赖由外部提供，而不是自己创建
   - 解耦组件，便于测试和维护
2. FastAPI的依赖注入：
   - 使用Depends函数
   - 自动解析函数参数
   - 支持嵌套依赖
3. 示例：
   ```python
   from fastapi import Depends, FastAPI
   
   app = FastAPI()
   
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   
   @app.get("/users/")
   def read_users(db: Session = Depends(get_db)):
       return db.query(User).all()
   ```
4. 优势：
   - 代码复用
   - 便于测试（mock依赖）
   - 生命周期管理

**评估要点：**
- 是否理解依赖注入的概念
- 是否能使用FastAPI的Depends
- 是否知道依赖注入的优势

---

## 题目5：Python的Web安全

**问题：** Python Web应用常见的安全问题有哪些？如何防范？

**标准答案：**
1. SQL注入：
   - 防范：使用ORM或参数化查询
   - Django/FastAPI ORM默认防注入
2. XSS（跨站脚本攻击）：
   - 防范：模板自动转义、Content-Security-Policy
3. CSRF（跨站请求伪造）：
   - 防范：使用CSRF Token
   - Django中间件自带CSRF保护
4. 文件上传漏洞：
   - 防范：验证文件类型、大小、存储位置
5. 认证和授权：
   - 使用HTTPS
   - 密码加盐哈希（bcrypt）
   - JWT Token安全
6. 依赖安全：
   - 定期更新依赖
   - 使用safety检查漏洞

**评估要点：**
- 是否了解常见Web安全问题
- 是否知道各框架的安全机制
- 是否能编写安全的Web代码
