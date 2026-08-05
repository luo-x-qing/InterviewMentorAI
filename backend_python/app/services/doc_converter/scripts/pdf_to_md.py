"""
PDF转Markdown转换器
将 PDF 题库（章节 + 数字编号题目 + 最简回答结构）重组为标准 MD 题库：
「## 题目N：标题 / **问题：** / **标准答案：**」，产物可被入库管道直接解析。

- 兼容字归一：CJK 兼容表意文字（⼀→一、⾯→面）经 NFKC 还原
- 内存转换：PdfConverter.to_markdown(path) 直接返回文本，供 import_document 单入口使用
- 落盘转换：convert_pdf_to_md(input, output) 写 MD 文件（CLI 用）
"""
import logging
import os
import re
import unicodedata

logger = logging.getLogger(__name__)

# 抑制 pdfminer 对无 FontBBox 字体的噪音警告
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)

# 章节行：NFKC 归一后为普通汉字「一、基础」
_SECTION_RE = re.compile(r"^[一二三四五六七八九十]{1,3}、")
# 题目行：题号 + 点/顿号后紧跟标题（无空格），如「1.String 区别」「2.反射机制」；
# 答案正文中的编号列表（「2. getClass」「3. 网络问题...」等，点后有空格）不视为题目
_QUESTION_RE = re.compile(r"^\d+[.、．]\S")
# 题号行中若命中以下特征，实为答案正文的编号列表项，不视为题目：
#   1) 以句号/冒号结尾（列表项「3. 网络问题...分发。」「1. 生产端：」）
#   2) 含反引号/方法签名（反射方法列表「2. `getClass()`...」）
#   3) 含可变参数签名（「7. `invoke(Object obj, Object... args)`...」）
_ANSWER_LINE_RE = re.compile(r"[。.：:]$|`|\(.*\.\.\.\s*\)")
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

    def extract_text(self, path: str) -> str:
        """pdfplumber 逐页提取文本，并对相邻页做跨页断行拼接"""
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            page_texts = [(page.extract_text() or "").strip() for page in pdf.pages]
        return self._merge_page_texts(page_texts)

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
            # 题号行但命中答案列表项特征（句号/冒号结尾、反引号、方法签名）→ 作为答案内容
            if m and not _ANSWER_LINE_RE.search(line):
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
