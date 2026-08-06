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


def _make_page(mocker, images=None, text="1.题目\n答案"):
    from PIL import Image

    page = mocker.Mock()
    page.images = images if images is not None else []
    page.extract_text.return_value = text
    fake_img = Image.new("RGB", (400, 400), (255, 255, 255))
    page.to_image.return_value = mocker.Mock(original=fake_img)
    return page


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

    def test_right_paren_numbered_question(self, mocker):
        """右括号题号（如 3 号 PDF「476) java 集合」）应独立成题"""
        md = _md(mocker, "27、解释Spring框架中bean的生命周期。\nSpring容器实例化bean。\n476) java 集合?\n集合常用类型。\n最简回答:集合")
        assert "## 题目1：27、解释Spring框架中bean的生命周期。" in md
        assert "## 题目2：476) java 集合?" in md


class TestAnswerListExclusion:
    """答案正文编号列表项不得误判为题号"""

    def test_space_after_dot_is_answer_line(self, mocker):
        md = _md(mocker, "1.反射机制\n以下是常用方法:\n2. getClass()\n3. getMethod()\n最简回答:动态获取")
        assert "## 题目2：" not in md
        assert "## 题目3：" not in md
        assert "2. getClass()" in md

    def test_space_after_dot_can_be_question(self, mocker):
        """「1. 线程的状态」等点后带空格的真实题目也应识别（修复 PDF 整章漏题）"""
        md = _md(mocker, "三、线程和锁\n1. 线程的状态\n在Java中线程有六种状态。\n2. 创建线程的方式\n继承Thread")
        assert "## 题目1：1. 线程的状态" in md
        assert "## 题目2：2. 创建线程的方式" in md

    def test_long_colon_explanation_is_answer_line(self, mocker):
        """「1. 原子性(Atomicity):事务中的操作要么...」长冒号解释为列表项，不判为题目"""
        md = _md(mocker, "1.事务ACID\n1. 原子性(Atomicity):事务中的操作要么全部成功,要么全部失败。\n最简回答:ACID")
        assert "## 题目2：" not in md
        assert "原子性(Atomicity)" in md

    def test_overlong_line_is_answer_line(self, mocker):
        """「1. Lambda表达式:...」题号+答案连体的超长行为列表项，不判为题目"""
        md = _md(mocker, "1.集合接口\n1. Lambda表达式:Lambda允许在Java中更简洁地使用函数式编程风格。它提供了一种简")
        assert "## 题目2：" not in md

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

    def test_medium_period_ending_is_question(self, mocker):
        """中等长度句号结尾的题号行（如 3 号 PDF「27、解释...生命周期。」）应独立成题"""
        md = _md(mocker,
                 "26、Spring框架中的单例bean是线程安全的吗?\n不,线程不安全。\n"
                 "27、解释Spring框架中bean的生命周期。\nSpring容器实例化bean。\n最简回答:生命周期")
        assert "## 题目1：26、Spring框架中的单例bean是线程安全的吗?" in md
        assert "## 题目2：27、解释Spring框架中bean的生命周期。" in md


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


class TestOcrIntegration:
    """PDF 图片 OCR：RapidOCR 离线识别并入对应页文本"""

    def _page(self, mocker, images=None, text="1.题目\n答案"):
        return _make_page(mocker, images, text)

    def test_ocr_disabled_returns_empty(self, mocker):
        from app.core.config import settings
        mocker.patch.object(settings, "pdf_ocr_enabled", False)
        c = _conv()
        page = self._page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}])
        assert c._ocr_page_images(page) == ""

    def test_page_without_images_returns_empty(self, mocker):
        c = _conv()
        page = self._page(mocker, images=[])
        assert c._ocr_page_images(page) == ""

    def test_ocr_extracts_image_text(self, mocker):
        from app.core.config import settings
        mocker.patch.object(settings, "pdf_ocr_enabled", True)
        mocker.patch.object(settings, "pdf_ocr_resolution", 300)

        class FakeOCR:
            def __init__(self):
                pass

            def __call__(self, crop):
                box = [[0, 0], [0, 0], [0, 0], [0, 0]]
                return ([[box, "双亲委派机制", 0.9],
                         [box, "逐级委托给父类加载器", 0.9]], 0.5)

        mocker.patch("rapidocr_onnxruntime.RapidOCR", return_value=FakeOCR())
        c = _conv()
        page = self._page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}])
        out = c._ocr_page_images(page)
        # OCR 文本行加「- 」前缀，避免编号行被误判为题号
        assert "图片内容：\n- 双亲委派机制\n- 逐级委托给父类加载器" == out

    def test_extract_text_appends_ocr_text(self, mocker):
        """含图页：页文本 + OCR 图片内容段，随后正常解析进题目答案"""
        from app.core.config import settings
        mocker.patch.object(settings, "pdf_ocr_enabled", True)

        import pdfplumber

        page = self._page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}],
                          text="1.类加载机制\n问题\n最简回答:委派")
        pdf = mocker.MagicMock()
        pdf.__enter__.return_value = pdf
        pdf.pages = [page]
        mocker.patch("pdfplumber.open", return_value=pdf)

        c = _conv()
        mocker.patch.object(c, "_ocr_page_images",
                            return_value="图片内容:\n- 3.准备:为类的静态变量分配内存,并设置默认初始值\n- 10.双亲委派机制")

        raw = c.extract_text("dummy.pdf")
        assert "最简回答:委派" in raw
        assert "图片内容:\n- 3.准备:为类的静态变量分配内存" in raw

        md = c.to_markdown("dummy.pdf")
        # md 经 NFKC 归一，OCR 段的全角冒号已转为半角
        assert "图片内容:\n- 3.准备:为类的静态变量分配内存,并设置默认初始值" in md
        assert "**标准答案：** 问题\n最简回答:委派\n图片内容:\n- 3.准备:为类的静态变量分配内存" in md

    def test_ocr_numbered_lines_not_parsed_as_questions(self, mocker):
        """图片内容段内的编号行（如 OCR 出的「3.准备：...」）不得被识别为新题目"""
        from app.core.config import settings
        mocker.patch.object(settings, "pdf_ocr_enabled", True)

        import pdfplumber

        page = self._page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}],
                          text="1.类加载机制\n问题\n最简回答:委派\n"
                               "2.反射机制\n答案反射")
        pdf = mocker.MagicMock()
        pdf.__enter__.return_value = pdf
        pdf.pages = [page]
        mocker.patch("pdfplumber.open", return_value=pdf)

        c = _conv()
        mocker.patch.object(c, "_ocr_page_images",
                            return_value="图片内容:\n- 3.准备:为类的静态变量分配内存,并设置默认初始值\n- 10.双亲委派机制")

        md = c.to_markdown("dummy.pdf")
        assert "## 题目2：3.准备" not in md
        assert "## 题目2：10.双亲委派机制" not in md
        assert "## 题目2：2.反射机制" in md
        assert "图片内容:\n- 3.准备:为类的静态变量分配内存,并设置默认初始值\n- 10.双亲委派机制" in md


class TestCidGarbagePages:
    """CID 乱码页（字体缺 ToUnicode 映射）：整页 OCR 替代文字层"""

    def test_is_cid_garbage_detects_cid(self):
        c = _conv()
        assert c._is_cid_garbage("(cid:1796)(cid:24073)）相比，(cid:1796)(cid:19716)(cid:8708)")
        assert not c._is_cid_garbage("正常的中文文本，没有乱码")
        assert not c._is_cid_garbage("")

    def test_cid_page_uses_full_ocr(self, mocker):
        """乱码页走整页 OCR，不再做图片区域 OCR"""
        import pdfplumber

        page = _make_page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}],
                          text="(cid:1796)(cid:24073)）相比，(cid:1796)(cid:19716)")
        pdf = mocker.MagicMock()
        pdf.__enter__.return_value = pdf
        pdf.pages = [page]
        mocker.patch("pdfplumber.open", return_value=pdf)

        c = _conv()
        mocker.patch.object(c, "_ocr_page_full",
                            return_value="1.什么 Spring beans\nSpring 容器负责创建和管理 Bean")
        mocker.patch.object(c, "_ocr_page_images", return_value="不应被调用")

        raw = c.extract_text("dummy.pdf")
        assert "Spring" in raw
        assert "(cid:" not in raw
        assert "不应被调用" not in raw
        c._ocr_page_images.assert_not_called()

    def test_clean_page_does_not_use_full_ocr(self, mocker):
        """正常文字页不做整页 OCR，图片区域 OCR 照常"""
        import pdfplumber

        page = _make_page(mocker, images=[{"x0": 0, "top": 0, "x1": 90, "bottom": 90}],
                          text="1.类加载机制\n答案")
        pdf = mocker.MagicMock()
        pdf.__enter__.return_value = pdf
        pdf.pages = [page]
        mocker.patch("pdfplumber.open", return_value=pdf)

        c = _conv()
        mocker.patch.object(c, "_ocr_page_full", return_value="不应被调用")
        mocker.patch.object(c, "_ocr_page_images", return_value="图片内容:\n- 双亲委派机制")

        raw = c.extract_text("dummy.pdf")
        assert "类加载机制" in raw
        assert "图片内容:\n- 双亲委派机制" in raw
        c._ocr_page_full.assert_not_called()
