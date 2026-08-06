"""
PDF转Markdown转换器
将 PDF 题库（章节 + 数字编号题目 + 最简回答结构）重组为标准 MD 题库：
「## 题目N：标题 / **问题：** / **标准答案：**」，产物可被入库管道直接解析。

- 兼容字归一：CJK 兼容表意文字（⼀→一、⾯→面）经 NFKC 还原
- 图片 OCR：图片区域文字经 RapidOCR（离线）识别，并入所在页题目答案
- 内存转换：PdfConverter.to_markdown(path) 直接返回文本，供 import_document 单入口使用
- 落盘转换：convert_pdf_to_md(input, output) 写 MD 文件（CLI 用）
"""
import logging
import os
import re
import unicodedata

from app.core.config import settings

logger = logging.getLogger(__name__)

# 抑制 pdfminer 对无 FontBBox 字体的噪音警告
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)

# 章节行：NFKC 归一后为普通汉字「一、基础」
_SECTION_RE = re.compile(r"^[一二三四五六七八九十]{1,3}、")
# 题目行：题号 + 点/顿号/右括号/右方括号后紧跟标题（允许后有空格，如「1. 线程的状态」；
# 兼容三种排版：「1.String 区别」「1. 线程的状态」「476) java 集合」都是题目）。
_QUESTION_RE = re.compile(r"^\d+[.、．)\]]\s*\S")
# 题号行中若命中以下特征，实为答案正文的编号列表项，不视为题目：
#   1) 以冒号/右括号结尾（列表项「1. 生产端：」「2. getClass()」）
#   2) 含反引号/方法签名（反射方法列表「2. `getClass()`...」）
#   3) 含可变参数签名（「7. `invoke(Object obj, Object... args)`...」）
#   4) 冒号后紧跟 16 字符以上的解释句（「1. 原子性(Atomicity):事务中的操作要么...」列表项）
# 句号结尾不在此列：题目行也可能以句号结尾（如「27、解释...bean的生命周期。」），
# 只在行很短（_ANSWER_PERIOD_MAX_LEN 内，典型的编号列表项）时视为列表项
_ANSWER_LINE_RE = re.compile(r"[:：]$|\)$|[:：](?=.{16})|`|\(.*\.\.\.\s*\)")
# 句号/点结尾的题号行：不超过此长度视为编号列表项；更长视为真实题目
_ANSWER_PERIOD_MAX_LEN = 15
# 题目行长度上限：超过视为「题号+答案连体」的列表项（「1. Lambda表达式:Lambda允许...」）
_MAX_TITLE_LEN = 50
# 上页末行若以此类标点结尾视为完整行，页边界保留换行；否则跨页拼接
_END_PUNCT_RE = re.compile(r"[。！？；;：:、%）」》】.~…!?]$")


class PdfConverter:
    """PDF 题库 → 标准 Markdown 题库转换器（题目级重组，适配 parse_questions）"""

    @staticmethod
    def _merge_page_texts(page_texts: list) -> str:
        """按页文本列表做跨页断行拼接

        逐页提取时页边界会把句子/标题截成两行（如「...接口文档内有什」+「么」），
        若上页末行不以终止标点结尾，则与下页首行合并。
        """
        if not page_texts:
            return ""
        merged = page_texts[0]
        for nxt in page_texts[1:]:
            if not nxt:
                # 空页：页间真实空白，阻断跨页拼接（上页末行视为完整行）
                merged = merged.rstrip("\n") + "\n"
                continue
            if merged.endswith("\n"):
                # 上页已完整结束（空页/完整末行），直接接续下一页
                merged = merged + nxt
                continue
            lines = merged.split("\n")
            head = nxt.split("\n")[0]
            # 上页末行无终止标点 → 与下页首行拼接（修复页边界断句）
            if lines and lines[-1] and not _END_PUNCT_RE.search(lines[-1]) and head:
                lines[-1] = lines[-1] + head
                merged = "\n".join(lines + nxt.split("\n")[1:])
            else:
                merged = merged + "\n" + nxt
        return merged

    @staticmethod
    def _is_cid_garbage(text: str) -> bool:
        """判定文字层是否为 CID 乱码（字体缺少 ToUnicode 映射，如 (cid:1540)）

        乱码页文字层不可用，需整页 OCR 替代。
        """
        if not text:
            return False
        cids = len(re.findall(r"\(cid:\d+\)", text))
        return cids / len(text) > 0.03

    def _ocr_page_full(self, page) -> str:
        """文字层为 CID 乱码的页面，整页渲染 + OCR 替代（离线）

        返回 OCR 识别的整页文本；OCR 不可用时优雅降级（返回空串，丢弃该页）。
        """
        if not settings.pdf_ocr_enabled:
            return ""
        try:
            import numpy as np
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            im = page.to_image(resolution=settings.pdf_ocr_resolution)
            arr = np.array(im.original.convert("RGB"))
        except Exception as e:
            logger.warning(f"整页 OCR 渲染失败: {e}")
            return ""
        try:
            result, _ = ocr(arr)
        except Exception as e:
            logger.debug(f"整页 OCR 失败: {e}")
            return ""
        if not result:
            return ""
        return "\n".join(line[1] for line in result)

    def extract_text(self, path: str) -> str:
        """pdfplumber 逐页提取文本；含图页做图片 OCR，CID 乱码页整页 OCR 替代"""
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            page_texts = []
            for page in pdf.pages:
                text = (page.extract_text() or "").strip()
                if self._is_cid_garbage(text):
                    # 文字层不可用：整页 OCR 替代（已含页面全部内容，无需再做图片 OCR）
                    full_ocr = self._ocr_page_full(page)
                    if full_ocr:
                        page_texts.append(full_ocr)
                    continue
                img_text = self._ocr_page_images(page)
                if img_text:
                    text = (text + "\n\n" + img_text).strip()
                page_texts.append(text)
        return self._merge_page_texts(page_texts)

    def _ocr_page_images(self, page) -> str:
        """渲染含图页 → 裁剪图片区域 → RapidOCR 识别（离线）

        图片区域文字作为该页题目的答案补充段返回；OCR 不可用时优雅降级（跳过图片）。
        """
        if not settings.pdf_ocr_enabled or not page.images:
            return ""
        try:
            import numpy as np
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            logger.warning("RapidOCR 未安装，跳过 PDF 图片文字提取")
            return ""

        try:
            ocr = RapidOCR()
            im = page.to_image(resolution=settings.pdf_ocr_resolution)
            arr = np.array(im.original.convert("RGB"))
        except Exception as e:
            logger.warning(f"图片渲染失败，跳过 OCR: {e}")
            return ""

        scale = settings.pdf_ocr_resolution / 72.0
        parts = []
        for img in page.images:
            x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
            y0, y1 = int(top * scale), int(bottom * scale)
            xl, xr = int(x0 * scale), int(x1 * scale)
            crop = arr[y0:y1, xl:xr]
            if crop.size == 0:
                continue
            try:
                result, _ = ocr(crop)
            except Exception as e:
                logger.debug(f"图片 OCR 失败: {e}")
                continue
            if result:
                # 每行加「- 」列表前缀：避免 OCR 出的编号行（如「3.准备：...」）
                # 在 to_markdown 里被 _QUESTION_RE 误判为新题目
                lines = [f"- {line[1]}" for line in result]
                parts.append("图片内容：\n" + "\n".join(lines))
        return "\n\n".join(parts)

    def to_markdown(self, path: str) -> str:
        """提取并重组为标准 MD 题库（## 题目N / **问题：** / **标准答案：**）"""
        raw = self.extract_text(path)
        # CJK 兼容字归一，使章节/题目识别稳定
        text = unicodedata.normalize("NFKC", raw)

        title = os.path.splitext(os.path.basename(path))[0]
        idx = 0
        cur_title = None
        answer_buf = []
        # (title, answer) 列表
        questions = []

        def finish() -> None:
            """收尾当前题目，追加到 questions"""
            questions.append((cur_title, "\n".join(answer_buf).strip()))

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # 章节行：收尾当前题并跳过（章节本身不入题）
            if _SECTION_RE.match(line):
                if cur_title is not None:
                    finish()
                    cur_title = None
                    answer_buf = []
                continue
            m = _QUESTION_RE.match(line)
            # 题号行但命中答案列表项特征（结尾标点/右括号/反引号/长冒号解释）→ 作为答案内容；
            # 句号结尾仅当行很短（编号列表项）时才视为答案行，中等长度句号行视为题目
            is_answer_line = bool(_ANSWER_LINE_RE.search(line)) or (
                bool(re.search(r"[。.]$", line)) and len(line) <= _ANSWER_PERIOD_MAX_LEN
            )
            if m and not is_answer_line and len(line) <= _MAX_TITLE_LEN:
                # 新题：先收尾上一题
                if cur_title is not None:
                    finish()
                idx += 1
                cur_title = line
                answer_buf = []
                continue
            # 题目行之间的内容累积为答案；首题前的无题头文本（前言）丢弃
            if cur_title is not None:
                answer_buf.append(line)

        if cur_title is not None:
            finish()

        # 后处理：空答案的题号行实为上一题答案中的编号列表项（如「1.生产者...重试」），
        # 并入上一题答案，避免把真实题目答案截断成碎片题
        merged = []
        for q_title, q_answer in questions:
            if q_answer or not merged:
                merged.append([q_title, q_answer])
            else:
                merged[-1][1] = (merged[-1][1] + "\n" + q_title).strip()

        # 输出标准题库格式（parse_questions 可解析）
        md_lines = [f"# {title}"]
        for i, (q_title, q_answer) in enumerate(merged, start=1):
            md_lines.append(f"## 题目{i}：{q_title}")
            md_lines.append(f"**问题：** {q_title}")
            md_lines.append(f"**标准答案：** {q_answer}")
            md_lines.append("")
        return "\n".join(md_lines)


def convert_pdf_to_md(input_path: str, output_path: str) -> bool:
    """将 PDF 题库转换为 Markdown 文件（CLI/批量转换入口）

    Returns:
        bool: 转换是否成功
    """
    try:
        content = PdfConverter().to_markdown(input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"PDF转换完成: {input_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"PDF转换失败: {e}")
        return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python pdf_to_md.py <输入PDF> <输出MD>")
        sys.exit(1)

    if convert_pdf_to_md(sys.argv[1], sys.argv[2]):
        sys.exit(0)
    sys.exit(1)
