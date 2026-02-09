"""Tenant management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.security import get_password_hash
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.admin import AdminCreate, AdminResponse
from app.schemas.tenant import TenantResponse, TenantUpdate
from app.services.audit import log_action

router = APIRouter()


@router.get("/me", response_model=TenantResponse)
def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the tenant associated with the authenticated user."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    return tenant


@router.patch("/me", response_model=TenantResponse)
def update_current_tenant(
    body: TenantUpdate,
    request: Request,
    current_user: User = Depends(require_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    """Update the current tenant's name or settings.

    Requires owner or admin role.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    log_action(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="tenant",
        resource_id=str(tenant.id),
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/me/admins", response_model=list[AdminResponse])
def list_tenant_admins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all admin users belonging to the current tenant."""
    admins = (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id)
        .order_by(User.created_at)
        .all()
    )
    return admins


@router.post(
    "/me/admins",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_admin(
    body: AdminCreate,
    request: Request,
    current_user: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    """Create a new admin user for the current tenant.

    Requires owner role. Cannot create owners via this endpoint.
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    new_user = User(
        tenant_id=current_user.tenant_id,
        email=body.email,
        password_hash=get_password_hash(body.password),
        full_name=body.full_name,
        role=UserRole(body.role),
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    log_action(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"email": body.email, "role": body.role},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(new_user)
    return new_user
