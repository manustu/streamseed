from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Project, User
from ..database import get_db
from .auth import get_current_user
from pydantic import BaseModel
from typing import List

# Create a FastAPI router for projects
router = APIRouter()

# Pydantic models for request and response validation
class ProjectCreate(BaseModel):
    name: str
    description: str
    status: str = "active"

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    user_id: int
    campaign_count: int

    class Config:
        orm_mode = True

# Endpoint to create a new project
@router.post("/projects/", response_model=ProjectResponse, tags=["projects"])
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        user_id=current_user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

# Endpoint to get a list of all projects
@router.get("/projects/", response_model=List[ProjectResponse], tags=["projects"])
def read_projects(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = (
        db.query(
            Project,
            func.count(Project.campaigns).label('campaign_count')  # Count the number of related campaigns
        )
        .filter(Project.user_id == current_user.id)
        .join(Project.campaigns, isouter=True)  # Left outer join to include projects with 0 campaigns
        .group_by(Project.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Map each tuple to a ProjectResponse instance
    project_responses = [
        ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            user_id=project.user_id,
            campaign_count=campaign_count
        )
        for project, campaign_count in projects
    ]

    return project_responses

# Endpoint to get a specific project by ID
@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def read_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Endpoint to delete a project
@router.delete("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return project
