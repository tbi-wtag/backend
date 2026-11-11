from typing import Any, Dict, Optional
from fastapi import Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import RateLimiter
from app.crud.audit_log import crud_audit_log
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def _extract_ip(request: Optional[Request]) -> str:
        return RateLimiter.get_real_ip(request) if request else "internal"

    @classmethod
    async def log_event(
        cls,
        db: AsyncSession,
        action: str,
        user_id: Optional[str] = None,
        status: str = "SUCCESS",
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        flush: bool = True,
    ) -> AuditLog:
        ip = cls._extract_ip(request)
        actor_label = f"user_id={user_id}" if user_id else f"ip={ip}"
        detail_str = f" | details={details}" if details else ""

        msg = (
            f"[AUDIT] [{action.upper()}] actor=({actor_label}) "
            f"status={status.upper()}{detail_str}"
        )
        if status.upper() == "SUCCESS":
            logger.info(msg)
        else:
            logger.warning(msg)

        return await crud_audit_log.create_audit_log(
            db=db,
            action=action,
            user_id=user_id,
            ip_address=ip,
            status=status,
            details=details,
            flush=flush,
        )


audit_service = AuditService()
