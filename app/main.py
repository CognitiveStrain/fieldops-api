import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.requests import Request

from .database import get_db
from .logging_config import configure_logging
from .models import User, WorkOrder
from .schemas import (
    SortBy,
    SortOrder,
    Token,
    UserCreate,
    UserRead,
    UserRoleUpdate,
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderUpdate,
)
from .security import (
    authenticate_user,
    create_access_token,
    ensure_bootstrap_admin,
    get_current_user,
    hash_password,
    normalize_email,
    require_roles,
)

configure_logging()
logger = logging.getLogger("fieldops.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_bootstrap_admin()
    yield


app = FastAPI(
    title="FieldOps API",
    version="1.2.0",
    description="Authenticated REST service for tracking engineering and operations work orders.",
    lifespan=lifespan,
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


@app.get("/")
def service_info() -> dict[str, str]:
    return {"service": "FieldOps API", "version": "1.2.0", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    email = normalize_email(str(payload.email))
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")

    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="viewer",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    db.refresh(user)
    return user


@app.post("/auth/token", response_model=Token)
def login_for_access_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = create_access_token(user)
    return Token(access_token=token, expires_in=expires_in)


@app.get("/auth/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return list(db.scalars(select(User).order_by(User.id.asc())))


@app.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@app.post("/work-orders", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(
    payload: WorkOrderCreate,
    current_user: User = Depends(require_roles("technician", "manager", "admin")),
    db: Session = Depends(get_db),
):
    item = WorkOrder(**payload.model_dump(), created_by_id=current_user.id)
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
    _: User = Depends(get_current_user),
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
def get_work_order(
    work_order_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    return item


@app.patch("/work-orders/{work_order_id}", response_model=WorkOrderRead)
def update_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    _: User = Depends(require_roles("technician", "manager", "admin")),
    db: Session = Depends(get_db),
):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/work-orders/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_order(
    work_order_id: int,
    _: User = Depends(require_roles("manager", "admin")),
    db: Session = Depends(get_db),
):
    item = db.get(WorkOrder, work_order_id)
    if not item:
        raise HTTPException(status_code=404, detail="work order not found")
    db.delete(item)
    db.commit()
