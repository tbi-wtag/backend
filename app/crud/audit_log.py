from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogUpdate


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogUpdate]):

    async def create_audit_log(
        self,
        db: AsyncSession,
        *,
        action: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        flush: bool = True,
    ) -> AuditLog:
        audit_in = AuditLogCreate(
            action=action.upper(),
            user_id=str(user_id) if user_id else None,
            ip_address=ip_address,
            status=status.upper(),
            details=details,
        )
        return await self.create(db, obj_in=audit_in, flush=flush)

    async def get_by_user_id(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        query = (
            select(self.model)
            .where(self.model.user_id == str(user_id))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


crud_audit_log = CRUDAuditLog(AuditLog)
