"""
Prompt 服务层
管理业务 prompt 模板，持有 LlmClient 进行调用
"""
import logging

from app.services.llm_client import LlmClient

logger = logging.getLogger(__name__)


class PromptService:
    """
    Prompt 服务类
    
    职责：管理业务 prompt 模板，组装参数后调用 LlmClient
    不直接操作 OpenAI 客户端
    """
    
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client
    
    def transcribe_interview(self, audio_file_path: str) -> str:
        """
        面试录音转录
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            转录的面试对话文本
        """
        system_prompt = """你是一个专业的面试录音转录助手。

你的任务是将面试录音转录为文字，并自动区分面试官和面试者的发言。

输出格式要求：
面试官：[面试官说的话]
面试者：[面试者说的话]
面试官：[面试官说的话]
面试者：[面试者说的话]
...

注意事项：
1. 准确识别每句话的说话人身份
2. 面试官通常是提问、追问、引导话题的一方
3. 面试者通常是回答问题、解释说明的一方
4. 保持对话的时间顺序
5. 只输出转录内容，不要添加任何分析或评价"""

        user_prompt = f"请转录以下面试录音：{audio_file_path}"
        
        return self.llm.call(system_prompt, user_prompt)
    
    def parse_dialogue(self, transcript: str) -> str:
        """
        说话人分离
        
        Args:
            transcript: 原始转录文本
            
        Returns:
            JSON 格式的对话列表
        """
        system_prompt = """你是一个专业的对话分析助手。

请分析以下面试对话，将其解析为结构化的 JSON 格式。

输出格式（JSON 数组）：
[
    {"speaker": "面试官", "content": "面试官说的话"},
    {"speaker": "面试者", "content": "面试者说的话"}
]

规则：
1. speaker 只能是 "面试官" 或 "面试者"
2. 保持对话的原始顺序
3. 只返回 JSON，不要添加其他说明"""

        user_prompt = f"请解析以下面试对话：\n\n{transcript}"
        
        return self.llm.call(system_prompt, user_prompt)
    
    def evaluate_answer(self, question: str, answer: str, ref_text: str = "") -> str:
        """
        评估面试者回答
        
        Args:
            question: 面试官的问题
            answer: 面试者的回答
            ref_text: 知识库参考资料（可选）
            
        Returns:
            JSON 格式的评估结果
        """
        system_prompt = """你是一个专业的面试评估专家。

请评估面试者的回答质量，给出以下信息（JSON 格式）：
{
    "score": 85,
    "level": "PROFICIENT",
    "strengths": "回答的优点",
    "weaknesses": "回答的不足",
    "correction": "修正方案",
    "knowledge_points": "拓展知识点"
}

评分标准：
- 90-100：优秀，回答准确、全面、有深度
- 70-89：良好，回答基本正确，有小瑕疵
- 60-69：及格，回答不够完整
- 0-59：薄弱，回答有明显错误或遗漏

注意：
- 只返回 JSON
- 熟练项的 correction 和 knowledge_points 可以为空字符串
- 如果提供了参考资料，请结合参考资料进行更准确的评估"""

        user_prompt = f"""请评估以下面试问答：

面试官问：{question}

面试者答：{answer}"""
        
        if ref_text:
            user_prompt += f"\n\n{ref_text}"
        
        return self.llm.call(system_prompt, user_prompt)
    
    def generate_report(self, evaluations: str) -> str:
        """
        生成面试复盘报告
        
        Args:
            evaluations: 所有评估结果的文本
            
        Returns:
            Markdown 格式的复盘报告
        """
        system_prompt = """你是一个专业的面试复盘报告生成助手。

请根据以下评估结果，生成一份完整的 Markdown 格式面试复盘报告。

报告结构：
# 面试复盘报告

## 总体评估
- 平均得分
- 熟练项数量
- 薄弱项数量

## 详细评估
每个问题的评估结果（使用 🟢 表示熟练，🟨 表示薄弱）

## 改进建议
针对薄弱项给出具体的改进建议

注意：
- 使用 Markdown 格式
- 语言简洁明了
- 突出重点"""

        user_prompt = f"请根据以下评估结果生成复盘报告：\n\n{evaluations}"
        
        return self.llm.call(system_prompt, user_prompt)
