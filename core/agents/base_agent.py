"""Agent 基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent 响应数据结构"""
    content: str
    agent_name: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_user_confirmation: bool = False
    suggested_actions: List[Dict] = field(default_factory=list)
    data: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "content": self.content,
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "requires_user_confirmation": self.requires_user_confirmation,
            "suggested_actions": self.suggested_actions,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Agent 基类

    所有专业 Agent 必须继承此类并实现核心方法
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: List[callable] = []

    @abstractmethod
    async def process(
        self,
        user_input: str,
        intent: str,
        entities: Dict[str, Any],
        context: Dict[str, Any],
        **kwargs
    ) -> AgentResponse:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            intent: 识别的意图
            entities: 提取的实体
            context: 对话上下文
            **kwargs: 其他参数

        Returns:
            AgentResponse: Agent 响应
        """
        pass

    @abstractmethod
    async def can_handle(self, intent: str) -> bool:
        """
        判断是否可以处理该意图

        Args:
            intent: 意图名称

        Returns:
            bool: 是否可以处理
        """
        pass

    def register_tool(self, tool: callable):
        """注册工具函数"""
        self.tools.append(tool)
        logger.info(f"✅ Tool registered to {self.name}: {tool.__name__}")

    async def use_tool(self, tool_name: str, **params) -> Any:
        """使用工具"""
        for tool in self.tools:
            if tool.__name__ == tool_name:
                try:
                    result = await tool(**params) if callable(tool) else None
                    logger.info(f"🔧 Tool used: {tool_name}")
                    return result
                except Exception as e:
                    logger.error(f"❌ Tool error: {tool_name}, {e}")
                    raise

        raise ValueError(f"Tool not found: {tool_name}")

    def _create_response(
        self,
        content: str,
        confidence: float = 1.0,
        **kwargs
    ) -> AgentResponse:
        """创建标准响应"""
        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=confidence,
            **kwargs
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name})>"
