"""
PdfConverter 单元测试（PDF 阶段）
验证：NFKC 兼容字归一、章节/题目/答案重组、标准 MD 输出、
答案列表项排除、空答案题号合并、跨页断行拼接、extract_text 页拼接。
"""
import os
import unicodedata
import pytest


def _conv():
    from app.services.doc_converter import PdfConverter
    return PdfConverter()


def _md(mocker, raw):
    c = _conv()
    mocker.patch.object(c, "extract_text", return_value=raw)
    return c.to_markdown("Java八股文.pdf")


class TestNfkcNormalization:
    """CJK 兼容字归一：⼀→一、⾯→面"""

    def test_merge_page_texts_normalizes_via_to_markdown(self, mocker):
        raw = "⼀、基础\n1.⾯试问题\n答案内容"
        md = _md(mocker, raw)

        # 兼容字 ⾯ 经 NFKC 归一为题目标题中的普通「面」
        assert "1.面试问题" in md
        assert "一、基础" not in md  # 章节行不入题


class TestStructure:
    """章节、题目、答案重组"""

    def test_chapter_and_questions(self, mocker):
        md = _md(mocker, "一、基础\n1.String 区别\n答案A\n最简回答:简\n"
                         "2.反射机制\n答案B\n二、并发\n3.线程池\n答案C")
        assert "## 题目1：1.String 区别" in md
        assert "## 题目2：2.反射机制" in md
        assert "## 题目3：3.线程池" in md
        assert "**标准答案：** 答案A\n最简回答:简" in md
        assert "**标准答案：** 答案C" in md
        assert "一、基础" not in md

    def test_question_before_first_section_is_kept(self, mocker):
        md = _md(mocker, "1.JVM 内存结构\n答案JVM\n二、基础\n2.String 区别\n答案S")
        assert "## 题目1：1.JVM 内存结构" in md
        assert "## 题目2：2.String 区别" in md

    def test_preamble_before_first_question_dropped(self, mocker):
        md = _md(mocker, "本资料仅供学习\n1.第一题\n答案")
        assert "本资料仅供学习" not in md
        assert "## 题目1：1.第一题" in md

    def test_answer_accumulates_until_next_question(self, mocker):
        md = _md(mocker, "1.第一题\n\n第一段\n第二段\n2.第二题\n答案")
        assert "**标准答案：** 第一段\n第二段" in md


class TestAnswerListExclusion:
    """答案正文编号列表项不得误判为题号"""

    def test_space_after_dot_is_answer_line(self, mocker):
        md = _md(mocker, "1.反射机制\n以下是常用方法:\n2. getClass()\n3. getMethod()\n最简回答:动态获取")
        assert "## 题目2：" not in md
        assert "## 题目3：" not in md
        assert "2. getClass()" in md

    def test_period_ending_is_answer_line(self, mocker):
        """句号结尾的编号行（如「2.消费者...分发。」）不被判为题号"""
        md = _md(mocker, "1.消息重复消费\n通常由以下原因:\n1.生产者重试,导致重复\n2.消费者错误,导致重新分发。\n最简回答:幂等")
        # 句号尾行并入上一题答案（不产生独立题目）
        assert "## 题目3：" not in md
        assert "2.消费者错误,导致重新分发。" in md

    def test_colon_ending_is_answer_line(self, mocker):
        md = _md(mocker, "1.接口规范\n标准五要素:\n1. 请求路径:\n2. 请求方式:\n最简回答:五要素")
        assert "## 题目2：" not in md
        assert "## 题目3：" not in md

    def test_backtick_method_signature_is_answer_line(self, mocker):
        md = _md(mocker, "1.反射方法\n1. `getClass()`:获取类型\n2. `invoke(Object obj, Object... args)`:调用方法\n最简回答:反射")
        assert "## 题目2：" not in md
        assert "`invoke(Object obj, Object... args)`" in md


class TestEmptyQuestionMerge:
    """无空答案的题号行（编号列表项）并入上一题答案，答案不截断"""

    def test_empty_question_merged_into_previous(self, mocker):
        raw = ("1.消息重复消费问题\n导致原因:\n"
               "1.生产者用于重试导致重复\n2.消费者处理错误\n3.网络问题\n"
               "2.如何保证幂等\n答案")
        md = _md(mocker, raw)

        assert "## 题目2：1.生产者用于重试导致重复" not in md
        assert "## 题目2：2.如何保证幂等" in md
        # 列表项并入题1 答案
        assert "生产者用于重试导致重复" in md


class TestPageMerge:
    """跨页断行拼接"""

    def test_incomplete_line_merged(self):
        c = _conv()
        out = c._merge_page_texts(["...接口文档内有什", "么\n🔔 接口文档由后端编写"])
        assert "...接口文档内有什么" in out

    def test_complete_line_kept_newline(self):
        c = _conv()
        out = c._merge_page_texts(["答案第一行。", "2.下一题\n答案"])
        assert "答案第一行。\n2.下一题" in out

    def test_empty_pages_skipped(self):
        c = _conv()
        out = c._merge_page_texts(["题1\n答案", "", "2.题2\n答案"])
        assert out == "题1\n答案\n2.题2\n答案"

    def test_to_markdown_calls_extract_text(self, mocker):
        c = _conv()
        mocker.patch.object(c, "extract_text", return_value="1.题\n答案")
        md = c.to_markdown(os.path.join("docs", "Java八股文.pdf"))
        assert md.startswith("# Java八股文")
