from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import WorkOrder
from .schemas import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FieldOps API",
    version="1.0.0",
    description="REST service for tracking engineering and operations work orders.",
)


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
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(WorkOrder).order_by(WorkOrder.id.desc())
    if status_filter:
        stmt = stmt.where(WorkOrder.status == status_filter)
    if priority:
        stmt = stmt.where(WorkOrder.priority == priority)
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
