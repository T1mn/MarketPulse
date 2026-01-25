"""Market 数据 API 路由"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from sources.binance import binance_service
from core.fetch_status import fetch_status_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class PriceResponse(BaseModel):
    """价格响应"""
    symbol: str
    price: float
    source: str  # "websocket" or "rest"
    timestamp: str


class Ticker24hResponse(BaseModel):
    """24h 统计响应"""
    symbol: str
    price_change: float
    price_change_percent: float
    last_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    source: str


class KlineResponse(BaseModel):
    """K 线响应"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


class FetchStatusResponse(BaseModel):
    """获取状态响应"""
    status: str
    description: Optional[str] = None
    error: Optional[str] = None


@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_price(symbol: str):
    """
    获取加密货币价格

    Args:
        symbol: 交易对 (如 BTCUSDT, ETHUSDT)
    """
    try:
        symbol = symbol.upper()
        price, source = await binance_service.get_price(symbol)

        return PriceResponse(
            symbol=price.symbol,
            price=price.price,
            source=source,
            timestamp=price.timestamp,
        )

    except Exception as e:
        logger.error(f"获取价格失败: {symbol}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}", response_model=Ticker24hResponse)
async def get_24h_ticker(symbol: str):
    """
    获取 24 小时行情统计

    Args:
        symbol: 交易对
    """
    try:
        symbol = symbol.upper()
        ticker, source = await binance_service.get_24h_ticker(symbol)

        return Ticker24hResponse(
            symbol=ticker.symbol,
            price_change=ticker.price_change,
            price_change_percent=ticker.price_change_percent,
            last_price=ticker.last_price,
            high_price=ticker.high_price,
            low_price=ticker.low_price,
            volume=ticker.volume,
            quote_volume=ticker.quote_volume,
            source=source,
        )

    except Exception as e:
        logger.error(f"获取 24h 统计失败: {symbol}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}", response_model=List[KlineResponse])
async def get_klines(
    symbol: str,
    interval: str = Query("1h", pattern="^(1m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    获取 K 线数据

    Args:
        symbol: 交易对
        interval: K 线周期 (1m, 15m, 1h, 4h, 1d)
        limit: 返回数量 (1-1000)
    """
    try:
        symbol = symbol.upper()
        klines = await binance_service.get_klines(symbol, interval, limit)

        return [
            KlineResponse(
                open_time=k.open_time,
                open=k.open,
                high=k.high,
                low=k.low,
                close=k.close,
                volume=k.volume,
                close_time=k.close_time,
            )
            for k in klines
        ]

    except Exception as e:
        logger.error(f"获取 K 线失败: {symbol} {interval}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=dict)
async def get_fetch_status():
    """获取所有数据源的获取状态"""
    return {
        "fetch_status": fetch_status_manager.get_all_status(),
        "websocket": binance_service.get_ws_status(),
    }


@router.get("/status/{source}", response_model=FetchStatusResponse)
async def get_source_status(source: str):
    """获取指定数据源的获取状态"""
    status = fetch_status_manager.get_status(source)
    return FetchStatusResponse(
        status=status["status"],
        description=status.get("description"),
        error=status.get("error"),
    )
