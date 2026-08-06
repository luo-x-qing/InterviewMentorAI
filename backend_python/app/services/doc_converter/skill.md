# 文档转换 Skill

## 作用
将不同格式的题库文档（PDF、Word、HTML、TXT等）转换为RAG系统可读的Markdown格式，存入知识库目录。

## 触发条件
当用户需要导入非`.md`或`.txt`格式的题库文档时，使用此skill。

## 工作流程

### 1. 检测文档格式
```python
# 支持的格式
SUPPORTED_FORMATS = {
    '.pdf': 'PDF文档',
    '.docx': 'Word文档',
    '.doc': 'Word旧格式',
    '.html': 'HTML网页',
    '.htm': 'HTML网页',
    '.txt': '纯文本',
    '.md': 'Markdown（无需转换）'
}
```

### 2. 调用对应转换脚本
```bash
# 转换命令格式
python app/services/doc_converter/scripts/convert.py --input <源文件路径> --output <输出目录>
```

### 3. 转换后处理
- 输出文件统一为`.md`格式
- 输出目录：`data/rag_docs/`
- 文件名保持原名，后缀改为`.md`

## 目录结构

```
doc_converter/
├── skill.md                    # 本说明文件
├── convert.py                  # 统一转换入口
├── __init__.py                 # 模块初始化
└── scripts/                    # 转换脚本目录
    ├── pdf_to_md.py           # PDF转换
    ├── docx_to_md.py          # Word转换
    ├── html_to_md.py          # HTML转换
    └── txt_to_md.py           # TXT转换
```

## 使用示例

### 转换单个文件
```bash
python app/services/doc_converter/scripts/convert.py \
    --input ./题库/Java面试题.pdf \
    --output ./data/rag_docs/
```

### 批量转换目录
```bash
python app/services/doc_converter/scripts/convert.py \
    --input ./题库/ \
    --output ./data/rag_docs/
```

### 指定转换格式
```bash
python app/services/doc_converter/scripts/convert.py \
    --input ./题库/Java面试题.pdf \
    --output ./data/rag_docs/ \
    --format md
```

## 依赖安装

```bash
# PDF转换
pip install PyPDF2 pdfplumber

# Word转换
pip install python-docx

# HTML转换
pip install beautifulsoup4

# OCR（PDF 图片文字，离线）
pip install rapidocr-onnxruntime
# onnxruntime 需 1.19.x：1.23+ 依赖更新的 VC++ 运行库，本机 DLL 加载失败
pip install onnxruntime==1.19.2
```

## 注意事项

1. **编码统一**：所有输出文件使用UTF-8编码
2. **格式清理**：移除多余空行、特殊字符
3. **表格处理**：保留表格结构，转换为Markdown表格
4. **图片处理**：含图页渲染 300dpi → 裁剪图片区域 → RapidOCR 离线识别，文本以 `图片内容:` + `- ` 列表行并入所在页题目答案（`- ` 前缀避免 OCR 编号行被误判为题号）；OCR 不可用时优雅降级跳过图片
5. **CID 乱码页整页 OCR**：缺 ToUnicode 映射的 PDF（如 485 页扫描版合集）文字层是 `(cid:xxxx)` 垃圾。`_is_cid_garbage(text)` 以 `(cid:\d+)` 占比 >3% 判定乱码页，`_ocr_page_full(page)` 整页渲染 300dpi + RapidOCR 替代文字层；正常页照旧走图片区域 OCR。入库侧 `knowledge_service` 另做块级兜底：任何含 `(cid:` 的块一律不入库
6. **题目识别规则**（`_QUESTION_RE`）：
   - 题号支持 `.` / `、` / `．` / `)` / `]` 分隔（如「476) java 集合」）
   - 行尾标点启发式：冒号/右括号结尾、含反引号/可变参数签名的行视为答案列表项，不判为题号
   - 句号结尾的题号行：行长 ≤15 字视为编号列表项（如「2.消费者错误,导致重新分发。」）；中等长度视为真实题目（如「27、解释...bean的生命周期。」），避免子题被并入上一题答案
   - 题号行长度上限 50 字，超长视为「题号+答案连体」列表项
7. **大文件处理**：超过10MB的文件会分块处理

## Agent执行指南

当收到文档转换任务时：

1. **先读取本skill.md**：了解转换流程和限制
2. **检测文件格式**：确认是否支持
3. **执行转换**：调用convert.py脚本
4. **验证结果**：检查输出文件是否正确
5. **更新知识库**：转换完成后运行rag_init.py入库

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 不支持的格式 | 提示用户，建议手动转换 |
| 文件损坏 | 跳过该文件，记录错误 |
| 编码问题 | 尝试多种编码（UTF-8, GBK, GB2312） |
| 依赖缺失 | 提示安装对应依赖 |
