"""
User roles enumeration for Role-Based Access Control (RBAC).
"""
from enum import Enum


class UserRole(Enum):
    """Enumeration for user roles in the system."""
    ADMIN = 'admin'
    REGULAR = 'regular'
    
    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Check if a role string is valid."""
        return role in [r.value for r in cls]
    
    @classmethod
    def get_default(cls) -> 'UserRole':
        """Get the default role for new users."""
        return cls.REGULAR
