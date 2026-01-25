"""Chatbot API 路由"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json

from core.dialogue.dialogue_manager import dialogue_manager
from api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口

    处理用户消息并返回 AI 响应
    """
    try:
        logger.info(f"📨 Chat request from user: {request.user_id}")

        # 使用对话管理器处理消息
        response = await dialogue_manager.process_message(
            user_input=request.message,
            session_id=request.session_id or f"session_{request.user_id}",
            user_id=request.user_id,
            language=request.language
        )

        # 构建响应
        chat_response = ChatResponse(
            content=response["content"],
            session_id=response["session_id"],
            intent=response["intent"],
            confidence=response["confidence"],
            agent=response["agent"],
            entities=response["entities"],
            suggested_actions=[],  # TODO: 从 Agent 响应中提取
            requires_confirmation=False,  # TODO: 从 Agent 响应中提取
        )

        logger.info(f"✅ Chat response sent: intent={response['intent']}, agent={response['agent']}")

        return chat_response

    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口

    使用 Server-Sent Events (SSE) 返回流式响应
    """
    async def generate():
        try:
            # 发送开始消息
            yield f"data: {json.dumps({'type': 'start', 'session_id': request.session_id or 'new'})}\n\n"

            # 处理消息（非流式，后续可优化为真正的流式）
            response = await dialogue_manager.process_message(
                user_input=request.message,
                session_id=request.session_id or f"session_{request.user_id}",
                user_id=request.user_id,
                language=request.language
            )

            # 发送内容
            yield f"data: {json.dumps({'type': 'content', 'content': response['content']})}\n\n"

            # 发送元数据
            metadata = {
                "type": "metadata",
                "metadata": {
                    "intent": response["intent"],
                    "confidence": response["confidence"],
                    "agent": response["agent"],
                    "entities": response["entities"],
                }
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # 发送完成消息
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 聊天接口

    支持实时双向通信
    """
    await websocket.accept()
    session_id = None

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            message = data.get("message")
            user_id = data.get("user_id")
            session_id = data.get("session_id") or f"ws_session_{user_id}"

            if not message or not user_id:
                await websocket.send_json({
                    "type": "error",
                    "error": "Missing message or user_id"
                })
                continue

            logger.info(f"🔌 WebSocket message from {user_id}: {message[:50]}...")

            # 处理消息
            response = await dialogue_manager.process_message(
                user_input=message,
                session_id=session_id,
                user_id=user_id,
                language=data.get("language", "zh-CN")
            )

            # 发送响应
            await websocket.send_json({
                "type": "response",
                "content": response["content"],
                "session_id": response["session_id"],
                "intent": response["intent"],
                "confidence": response["confidence"],
                "agent": response["agent"],
                "entities": response["entities"],
            })

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
