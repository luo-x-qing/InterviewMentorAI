"""
LLM 底层客户端
封装 OpenAI 兼容接口，提供通用的 LLM 调用能力
"""
import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import LlmError

logger = logging.getLogger(__name__)


class LlmClient:
    """
    LLM 底层通信客户端
    
    职责：仅负责 OpenAI 客户端初始化和通用调用
    不包含任何业务 prompt 逻辑
    """
    
    def __init__(self):
        self.api_key = settings.dashscope_api_key
        self.model_name = settings.llm_model_name
        self.temperature = settings.llm_temperature
        self.base_url = settings.llm_base_url
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def call(self, system_prompt: str, user_prompt: str) -> str:
        """
        底层 LLM 调用
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            
        Returns:
            大模型回复文本
        """
        logger.info(f"调用千问大模型, model={self.model_name}")
        
        try:
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                stream=False
            )
            
            reply = completion.choices[0].message.content
            logger.info(f"调用成功, response_length={len(reply) if reply else 0}")
            
            return reply if reply else ""
            
        except Exception as e:
            logger.error(f"千问大模型调用异常: {e}")
            raise LlmError(f"千问调用失败: {str(e)}")
