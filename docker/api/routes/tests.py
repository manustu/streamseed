from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models import Project, User
from ..database import get_db
from .auth import get_current_user
from pydantic import BaseModel
from typing import List

# Create a FastAPI router for projects
# Create a router with redirect_slashes set to False
router = APIRouter(
    redirect_slashes=False
)

# Pydantic models for request and response validation
class Test(BaseModel):
    name: str
    description: str
    status: str = "active"

@router.get("/some_protected_route")
def some_protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.first_name}"}