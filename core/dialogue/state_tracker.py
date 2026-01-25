"""对话状态追踪器 - Dialogue State Tracking (DST)"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class DialogueState:
    """对话状态"""
    session_id: str
    user_id: str
    current_intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    context: List[Dict] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_intent": self.current_intent,
            "entities": self.entities,
            "context": self.context,
            "variables": self.variables,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DialogueState":
        """从字典创建"""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            current_intent=data.get("current_intent"),
            entities=data.get("entities", {}),
            context=data.get("context", []),
            variables=data.get("variables", {}),
            turn_count=data.get("turn_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class DialogueStateTracker:
    """
    对话状态追踪器

    功能：
    1. 管理对话状态
    2. 跟踪上下文信息
    3. 管理实体槽位
    4. 处理多轮对话
    """

    def __init__(self, max_context_size: int = 10):
        self.max_context_size = max_context_size
        self.states: Dict[str, DialogueState] = {}

    def get_or_create_state(
        self,
        session_id: str,
        user_id: str
    ) -> DialogueState:
        """获取或创建对话状态"""
        if session_id not in self.states:
            self.states[session_id] = DialogueState(
                session_id=session_id,
                user_id=user_id
            )
            logger.info(f"📝 Created new dialogue state: {session_id}")

        return self.states[session_id]

    def update_state(
        self,
        session_id: str,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
        user_message: Optional[str] = None,
        assistant_message: Optional[str] = None,
        **variables
    ):
        """更新对话状态"""
        state = self.states.get(session_id)
        if not state:
            logger.warning(f"State not found: {session_id}")
            return

        # 更新意图
        if intent:
            state.current_intent = intent

        # 更新实体（合并新实体）
        if entities:
            state.entities.update(entities)

        # 添加上下文
        if user_message:
            state.context.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })

        if assistant_message:
            state.context.append({
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.now().isoformat()
            })

        # 限制上下文大小
        if len(state.context) > self.max_context_size:
            state.context = state.context[-self.max_context_size:]

        # 更新变量
        state.variables.update(variables)

        # 增加轮次
        state.turn_count += 1
        state.updated_at = datetime.now()

        logger.info(
            f"📝 Updated state: {session_id}, intent={intent}, "
            f"entities={len(state.entities)}, turn={state.turn_count}"
        )

    def get_context(
        self,
        session_id: str,
        last_n: Optional[int] = None
    ) -> List[Dict]:
        """获取对话上下文"""
        state = self.states.get(session_id)
        if not state:
            return []

        context = state.context
        if last_n:
            context = context[-last_n:]

        return context

    def get_entities(self, session_id: str) -> Dict:
        """获取实体信息"""
        state = self.states.get(session_id)
        if not state:
            return {}

        return state.entities.copy()

    def clear_entities(self, session_id: str):
        """清除实体"""
        state = self.states.get(session_id)
        if state:
            state.entities = {}

    def set_variable(self, session_id: str, key: str, value: Any):
        """设置变量"""
        state = self.states.get(session_id)
        if state:
            state.variables[key] = value

    def get_variable(self, session_id: str, key: str, default: Any = None) -> Any:
        """获取变量"""
        state = self.states.get(session_id)
        if state:
            return state.variables.get(key, default)
        return default

    def delete_state(self, session_id: str):
        """删除对话状态"""
        if session_id in self.states:
            del self.states[session_id]
            logger.info(f"🗑️ Deleted state: {session_id}")

    def export_state(self, session_id: str) -> Optional[str]:
        """导出状态为 JSON"""
        state = self.states.get(session_id)
        if state:
            return json.dumps(state.to_dict(), ensure_ascii=False, indent=2)
        return None

    def import_state(self, state_json: str) -> bool:
        """导入状态"""
        try:
            data = json.loads(state_json)
            state = DialogueState.from_dict(data)
            self.states[state.session_id] = state
            logger.info(f"📥 Imported state: {state.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to import state: {e}")
            return False

    def get_active_sessions(self) -> List[str]:
        """获取所有活跃会话"""
        return list(self.states.keys())

    def cleanup_old_sessions(self, max_age_minutes: int = 30):
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = []

        for session_id, state in self.states.items():
            age = (now - state.updated_at).total_seconds() / 60
            if age > max_age_minutes:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.delete_state(session_id)

        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


# 全局状态追踪器实例
dialogue_state_tracker = DialogueStateTracker()
