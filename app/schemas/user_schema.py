# app/schemas/user_schema.py
"""
Pydantic schemas for user endpoints.

This file is written to be compatible with both pydantic v1 and v2:
- It detects major pydantic version and exposes either `Config.orm_mode = True`
  (v1) or `model_config = {"from_attributes": True}` (v2) via an inherited mixin.
- Avoids defining both `Config` and `model_config` on the same class.
"""

from typing import Optional, Any
from pydantic import BaseModel

# Try to import EmailStr if available (requires email-validator)
try:
    from pydantic import EmailStr  # type: ignore
except Exception:
    EmailStr = str  # fallback to plain str if email-validator not installed

# Detect pydantic major version (best-effort, no external dependency)
_pyd_ver = getattr(__import__("pydantic"), "__version__", "2.0")
try:
    _pyd_major = int(str(_pyd_ver).split(".")[0])
except Exception:
    _pyd_major = 2

if _pyd_major >= 2:
    # For pydantic v2: provide model_config only
    class OrmConfigMixin:
        model_config = {"from_attributes": True}
else:
    # For pydantic v1: provide Config.orm_mode only
    class OrmConfigMixin:
        class Config:
            orm_mode = True


class UserCreate(BaseModel, OrmConfigMixin):
    email: EmailStr
    password: str  # caller-side validation: min length enforced in router/validator
    name: Optional[str] = None


class UserOut(BaseModel, OrmConfigMixin):
    id: int
    email: EmailStr
    name: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class TokenOut(BaseModel, OrmConfigMixin):
    access_token: str
    token_type: str = "bearer"
