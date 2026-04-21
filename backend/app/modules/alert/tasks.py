"""
预留给异步 worker 的任务入口。
比赛版本先走同步 API；后续若接入 Celery / Redis，可将社区风险引擎
从接口触发改为异步任务触发，并在任务完成后推送到驾驶舱缓存或 WebSocket。
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


def enqueue_alert_engine_run(*args, **kwargs) -> dict:
    logger.info('alert engine task placeholder called, args=%s kwargs=%s', args, kwargs)
    return {'queued': False, 'message': 'worker placeholder only'}
