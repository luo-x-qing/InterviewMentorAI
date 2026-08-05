"""
数据清洗服务（P1 · ADR-0002 D1/D2 落地）
纯函数，无 IO，可单测：清洗 → 解析 → 指纹
"""
import hashlib
import re
from typing import NamedTuple
from app.models.schemas import Question

# 题目字段标签（兼容题库变体）
_QUESTION_LABELS = "问题|题目"
_ANSWER_LABELS = "标准答案|参考答案|标准答案要点|参考答案要点"
_EVALUATION_LABELS = "评估要点"
_ALL_FIELD_LABELS = "|".join((_QUESTION_LABELS, _ANSWER_LABELS, _EVALUATION_LABELS))


class _ParsedHead(NamedTuple):
    """题目段头解析结果"""

    question_no: str
    title: str


class CleaningService:
    """数据清洗服务"""

    def clean_text(self, text: str) -> str:
        """文本清洗：去 BOM/控制字符/行尾空白/压缩空行/合并分隔线，去首尾空白"""
        if not text:
            return ""

        # 去 BOM
        text = text.lstrip("\ufeff")

        # 移除控制字符（保留 \n \t）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # 行尾空格与制表符清理
        lines = [line.rstrip(" \t") for line in text.split("\n")]
        text = "\n".join(lines)

        # 压缩连续空行（段落间最多一个空行）
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 合并重复分隔线（连续 --- 及其中空行归并为一行）
        merged_lines = []
        prev_was_divider = False
        for line in text.split("\n"):
            if re.fullmatch(r"-{3,}[ \t]*", line):
                if not prev_was_divider:
                    merged_lines.append("---")
                prev_was_divider = True
            elif line == "":
                if not prev_was_divider:
                    merged_lines.append(line)
            else:
                prev_was_divider = False
                merged_lines.append(line)
        text = "\n".join(merged_lines)

        # 去首尾空白
        return text.strip()

    def parse_questions(self, text: str, source: str = "") -> list[Question]:
        """题库结构解析：抽取结构化题目列表"""
        if not text:
            return []

        questions = []
        # 按 '## ' 标题切分（文件头等无编号段在解析头时跳过）
        sections = re.split(r"(?=^##\s)", text, flags=re.M)
        for section in sections:
            section = section.strip()
            if not section:
                continue
            head_line = section.split("\n", 1)[0]
            parsed_head = self._parse_head(head_line)
            if parsed_head is None:
                continue
            # 仅解析含「问题/题目」标签的题目段；无 Q 的参考段（如技术难点标准答案）不算题目
            if not re.search(r"\*\*(?:" + _QUESTION_LABELS + r")\s*[：:]", section):
                continue
            questions.append(Question(
                question_no=parsed_head.question_no,
                title=parsed_head.title,
                question=self._extract_field(section, _QUESTION_LABELS),
                answer=self._extract_field(section, _ANSWER_LABELS),
                evaluation_points=self._extract_field(section, _EVALUATION_LABELS),
                source=source,
            ))
        return questions

    @staticmethod
    def _parse_head(line: str) -> _ParsedHead | None:
        """解析 '## 题目N：标题' / '## 第N题：标题' / '## N. 标题'"""
        m = re.match(r"^##\s+(?:题目\s*(\d+)|第\s*(\d+)\s*题)[：:]\s*(.+)$", line)
        if m:
            return _ParsedHead(m.group(1) or m.group(2), m.group(3).strip())
        m2 = re.match(r"^##\s+(\d+)[.、．]\s*(.+)$", line)
        if m2:
            return _ParsedHead(m2.group(1), m2.group(2).strip())
        return None

    @staticmethod
    def _extract_field(section: str, tag_pattern: str) -> str:
        """抽取 **标签：** 到下一个已知字段标签或段尾之间的内容"""
        stop = r"(?=\n\*\*(?:" + _ALL_FIELD_LABELS + r")\s*[：:]|\Z)"
        m = re.search(r"\*\*(?:" + tag_pattern + r")\s*[：:]\*\*(.*?)" + stop, section, re.DOTALL)
        if not m:
            return ""
        return m.group(1).strip()

    @staticmethod
    def fingerprint(content: str) -> str:
        """内容指纹：用于幂等去重与变更检测"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()
