# routes/projects.py

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Project, User, Campaign
from ..database import get_db
from .auth import get_current_user
from pydantic import BaseModel
from .campaigns import CampaignResponse, compute_campaign_status

router = APIRouter()

# Pydantic models for request and response validation

class ProjectCreate(BaseModel):
    name: str
    description: str

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str  # Computed status based on campaign dates
    user_id: int
    campaign_count: int
    earliest_campaign_start: Optional[date] = None
    latest_campaign_end: Optional[date] = None

    model_config = {
        "from_attributes": True  # Updated for Pydantic v2
    }

# Helper function to convert Project to ProjectResponse
def project_to_response(
    project: Project,
    campaign_count: int,
    earliest_campaign_start: Optional[date],
    latest_campaign_end: Optional[date]
) -> ProjectResponse:
    current_date = date.today()
    
    # Determine the status based on campaign dates
    if earliest_campaign_start and latest_campaign_end:
        if earliest_campaign_start <= current_date <= latest_campaign_end:
            computed_status = "Active"
        elif current_date < earliest_campaign_start:
            computed_status = "Pending"
        elif current_date > latest_campaign_end:
            computed_status = "Ended"
    else:
        # Define default status when there are no campaigns
        computed_status = "Not Started"  # Adjust based on your business logic
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=computed_status,
        user_id=project.user_id,
        campaign_count=campaign_count,
        earliest_campaign_start=earliest_campaign_start,
        latest_campaign_end=latest_campaign_end
    )

# Endpoint to create a new project
@router.post("/projects", response_model=ProjectResponse, tags=["projects"])
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    new_project = Project(
        name=project.name,
        description=project.description,
        user_id=current_user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return project_to_response(
        new_project, 
        campaign_count=0, 
        earliest_campaign_start=None, 
        latest_campaign_end=None
    )

# Endpoint to get a list of all projects
@router.get("/projects", response_model=List[ProjectResponse], tags=["projects"])
def read_projects(
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    projects = (
        db.query(
            Project,
            func.count(Campaign.id).label('campaign_count'),
            func.min(Campaign.start_date).label('earliest_campaign_start'),
            func.max(Campaign.end_date).label('latest_campaign_end')
        )
        .outerjoin(Campaign, Campaign.project_id == Project.id)
        .filter(Project.user_id == current_user.id)
        .group_by(Project.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        project_to_response(
            project, 
            campaign_count, 
            earliest_campaign_start, 
            latest_campaign_end
        )
        for project, campaign_count, earliest_campaign_start, latest_campaign_end in projects
    ]

# Endpoint to get a specific project by ID
@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def read_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project_data = (
        db.query(
            Project,
            func.count(Campaign.id).label('campaign_count'),
            func.min(Campaign.start_date).label('earliest_campaign_start'),
            func.max(Campaign.end_date).label('latest_campaign_end')
        )
        .outerjoin(Campaign, Campaign.project_id == Project.id)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .group_by(Project.id)
        .first()
    )
    
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project, campaign_count, earliest_campaign_start, latest_campaign_end = project_data

    return project_to_response(
        project, 
        campaign_count, 
        earliest_campaign_start, 
        latest_campaign_end
    )

# Endpoint to delete a project
@router.delete("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project_data = (
        db.query(
            Project,
            func.count(Campaign.id).label('campaign_count'),
            func.min(Campaign.start_date).label('earliest_campaign_start'),
            func.max(Campaign.end_date).label('latest_campaign_end')
        )
        .outerjoin(Campaign, Campaign.project_id == Project.id)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .group_by(Project.id)
        .first()
    )
    
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project, campaign_count, earliest_campaign_start, latest_campaign_end = project_data

    # Compute status before deletion
    response = project_to_response(
        project, 
        campaign_count, 
        earliest_campaign_start, 
        latest_campaign_end
    )
    
    db.delete(project)
    db.commit()
    
    return response

# Endpoint to get a list of campaigns by project
@router.get("/projects/{project_id}/campaigns", response_model=List[CampaignResponse], tags=["projects"])
def read_campaigns_by_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verify that the project exists and belongs to the current user
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not authorized")
    
    # Fetch campaigns associated with the project
    campaigns = db.query(Campaign).filter(Campaign.project_id == project_id).all()
    
    # Compute status for each campaign and include project_name
    return [
        CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            project_id=campaign.project_id,
            project_name=project.name,  # Assign Project Name
            requirements=campaign.requirements,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            computed_status=compute_campaign_status(campaign)
        )
        for campaign in campaigns
    ]
