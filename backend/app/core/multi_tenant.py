"""Multi-tenant context management using contextvars.

Provides thread-safe, async-safe tenant context for request isolation.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID


# Context variable for current tenant ID
_current_tenant_id: ContextVar[Optional[UUID]] = ContextVar(
    "current_tenant_id", default=None
)


class TenantContext:
    """Thread-safe tenant context manager.

    Uses Python's contextvars for async-safe request isolation.
    Each request maintains its own tenant context without interfering
    with concurrent requests.

    Example:
        >>> TenantContext.set_tenant(UUID("..."))
        >>> current = TenantContext.get_tenant()
        >>> TenantContext.clear()
    """

    @staticmethod
    def set_tenant(tenant_id: UUID) -> None:
        """Set the current tenant ID for this context.

        Args:
            tenant_id: UUID of the tenant/client.
        """
        _current_tenant_id.set(tenant_id)

    @staticmethod
    def get_tenant() -> Optional[UUID]:
        """Get the current tenant ID.

        Returns:
            UUID of the current tenant, or None if not set.
        """
        return _current_tenant_id.get()

    @staticmethod
    def clear() -> None:
        """Clear the current tenant context."""
        _current_tenant_id.set(None)

    @staticmethod
    def require_tenant() -> UUID:
        """Get the current tenant ID, raising if not set.

        Returns:
            UUID of the current tenant.

        Raises:
            ValueError: If no tenant context is set.
        """
        tenant_id = _current_tenant_id.get()
        if tenant_id is None:
            raise ValueError("No tenant context set. Ensure middleware is configured.")
        return tenant_id

    @staticmethod
    def validate_tenant(expected_tenant_id: UUID) -> None:
        """Validate that the current tenant matches the expected tenant.

        Args:
            expected_tenant_id: The expected tenant UUID.

        Raises:
            ValueError: If tenant context doesn't match or is not set.
        """
        current = TenantContext.get_tenant()
        if current is None:
            raise ValueError("No tenant context set.")
        if current != expected_tenant_id:
            raise ValueError(
                f"Tenant mismatch: context has {current}, expected {expected_tenant_id}"
            )
