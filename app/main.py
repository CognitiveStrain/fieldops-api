import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from .database import get_db
from .logging_config import configure_logging
from .models import WorkOrder
from .schemas import SortBy, SortOrder, WorkOrderCreate, WorkOrderRead, WorkOrderUpdate

configure_logging()
logger = logging.getLogger("fieldops.api")

app = FastAPI(
    title="FieldOps API",
    version="1.1.0",
    description="REST service for tracking engineering and operations work orders.",
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/work-orders", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    item = WorkOrder(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/work-orders", response_model=list[WorkOrderRead])
def list_work_orders(
    response: Response,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    assignee: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    sort_by: SortBy = "id",
    sort_order: SortOrder = "desc",
    db: Session = Depends(get_db),
):
    filters = []
    if status_filter:
        filters.append(WorkOrder.status == status_filter)
    if priority:
        filters.append(WorkOrder.priority == priority)
    if assignee:
        filters.append(WorkOrder.assignee == assignee)

    total = db.scalar(select(func.count()).select_from(WorkOrder).where(*filters)) or 0
    response.headers["X-Total-Count"] = str(total)

    sort_column = getattr(WorkOrder, sort_by)
    order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    stmt = select(WorkOrder).where(*filters).order_by(order_clause).offset(offset).limit(limit)
    return list(db.scalars(stmt))


@app.get("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def get_work_order(work_order_id: int, db: Session = Depends(get_db)):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    return item


@app.patch("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def update_work_order(work_order_id: int, payload: WorkOrderUpdate, db: Session = Depends(get_db)):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/work-orders/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_order(work_order_id: int, db: Session = Depends(get_db)):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    db.delete(item)
    db.commit()
