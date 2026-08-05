"""
CleaningService 单元测试
测试接缝: CleaningService.clean_text() / parse_questions() / fingerprint()
"""
import pytest
from app.services.cleaning_service import CleaningService


class TestFingerprint:
    """内容指纹测试（T1.3）"""

    def test_same_text_same_fingerprint(self):
        assert CleaningService.fingerprint("Python列表") == CleaningService.fingerprint("Python列表")

    def test_diff_text_diff_fingerprint(self):
        assert CleaningService.fingerprint("列表") != CleaningService.fingerprint("元组")

    def test_fingerprint_returns_md5_hex(self):
        assert len(CleaningService.fingerprint("abc")) == 32
        assert CleaningService.fingerprint("abc").isalnum()

    def test_empty_content(self):
        assert CleaningService.fingerprint("") == CleaningService.fingerprint("")


class TestCleanText:
    """文本清洗测试（T1.1）"""

    def test_removes_bom(self):
        result = CleaningService().clean_text("\ufeff# Python基础面试题")
        assert result == "# Python基础面试题"

    def test_compresses_multiple_blank_lines(self):
        text = "第一段\n\n\n\n\n第二段"
        assert CleaningService().clean_text(text) == "第一段\n\n第二段"

    def test_removes_control_chars(self):
        assert CleaningService().clean_text("正常内容\x00\x1f\x7f内容") == "正常内容内容"

    def test_merges_repeated_dividers(self):
        text = "---\n\n---\n\n---"
        assert CleaningService().clean_text(text) == "---"

    def test_trims_trailing_spaces(self):
        assert CleaningService().clean_text("第一行   \n第二行\t") == "第一行\n第二行"

    def test_strips_outer_whitespace(self):
        assert CleaningService().clean_text("  \n# 标题\n  ") == "# 标题"

    def test_empty_text(self):
        assert CleaningService().clean_text("") == ""
        assert CleaningService().clean_text("   \n\n  ") == ""


SAMPLE_Q1 = """## 题目1：Python列表和元组的区别

**问题：** 请比较Python列表和元组的区别。

**标准答案：**
1. 可变性：
   - 列表（list）：可变，可以修改元素
   - 元组（tuple）：不可变

**评估要点：**
- 是否理解可变性差异
- 是否能根据场景选择合适的数据结构
"""

SAMPLE_TWO = """## 题目1：列表和元组的区别

**问题：** 请比较列表和元组的区别。

**标准答案：** 列表可变，元组不可变。

---

## 题目2：深拷贝和浅拷贝

**问题：** 请解释深拷贝和浅拷贝的区别。

**标准答案：** 深拷贝递归复制，浅拷贝只复制引用。
"""

SAMPLE_VARIANT = """## 题目3：Python的装饰器

**题目：** 什么是Python装饰器？请举例说明。

**参考答案：** 装饰器是一个函数，接受函数作为参数。

**评估要点：**
- 理解闭包
"""


class TestParseQuestions:
    """题库结构解析测试（T1.2）"""

    def test_parse_single_standard_question(self):
        qs = CleaningService().parse_questions(SAMPLE_Q1, source="Python基础面试题.md")
        assert len(qs) == 1
        q = qs[0]
        assert q.question_no == "1"
        assert q.title == "Python列表和元组的区别"
        assert q.question == "请比较Python列表和元组的区别。"
        assert "1. 可变性" in q.answer
        assert "- 是否理解可变性差异" in q.evaluation_points
        assert q.source == "Python基础面试题.md"

    def test_parse_multiple_questions_in_order(self):
        qs = CleaningService().parse_questions(SAMPLE_TWO, source="JVM面试题.md")
        assert len(qs) == 2
        assert qs[0].question_no == "1"
        assert qs[1].question_no == "2"
        assert qs[0].title == "列表和元组的区别"
        assert qs[1].title == "深拷贝和浅拷贝"

    def test_variant_tags(self):
        qs = CleaningService().parse_questions(SAMPLE_VARIANT, source="Python基础面试题.md")
        assert len(qs) == 1
        q = qs[0]
        assert q.question == "什么是Python装饰器？请举例说明。"
        assert "装饰器是一个函数" in q.answer
        assert "理解闭包" in q.evaluation_points

    def test_missing_evaluation_points(self):
        text = """## 题目1：JVM内存区域划分

**问题：** JVM有哪些内存区域？

**标准答案：** 方法区、堆、栈、程序计数器。
"""
        qs = CleaningService().parse_questions(text)
        assert len(qs) == 1
        assert qs[0].evaluation_points == ""

    def test_missing_answer(self):
        text = """## 题目1：类加载机制

**问题：** 类加载有哪几个阶段？
"""
        qs = CleaningService().parse_questions(text)
        assert len(qs) == 1
        assert qs[0].answer == ""
        assert "类加载" in qs[0].question

    def test_empty_text(self):
        assert CleaningService().parse_questions("") == []

    def test_reference_file_not_parsed_as_question(self):
        text = """## 1. Java集合框架

### HashMap底层原理

**标准答案要点：**
- 基于数组+链表+红黑树

**优秀回答应包含：**
- 线程不安全
"""
        assert CleaningService().parse_questions(text) == []

    def test_answer_points_variant(self):
        """兼容「**标准答案要点：**」答案变体"""
        text = """## 题目1：HashMap底层原理

**问题：** 描述HashMap的存储结构。

**标准答案要点：**
- 数组+链表+红黑树
"""
        qs = CleaningService().parse_questions(text)
        assert len(qs) == 1
        assert "红黑树" in qs[0].answer
        assert "HashMap" in qs[0].question
