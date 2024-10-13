# routes/campaigns.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models import Campaign, User, Project
from ..database import get_db
from .auth import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

router = APIRouter()

# Pydantic models for request and response validation

class CampaignCreate(BaseModel):
    name: str
    description: str
    project_id: int
    requirements: str
    start_date: date
    end_date: date

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: str
    project_id: int
    project_name: str  # New field for Project Name
    requirements: str
    start_date: date
    end_date: date
    computed_status: str  # Dynamically computed status

    model_config = {
        "from_attributes": True  # Updated for Pydantic v2
    }

class CampaignUpdateRequest(BaseModel):
    reason: Optional[str] = None
    name: Optional[str] = Field(None, example="Updated Campaign Name")
    description: Optional[str] = Field(None, example="Updated description")
    project_id: Optional[int] = Field(None, example=2)
    requirements: Optional[str] = Field(None, example="Updated requirements")
    start_date: Optional[date] = Field(None, example="2024-01-01")
    end_date: Optional[date] = Field(None, example="2024-12-31")
    
    model_config = {
        "from_attributes": True  # Updated for Pydantic v2
    }

# Response model for the update operation
class CampaignUpdateResponse(BaseModel):
    success: bool
    reason: Optional[str] = None

class DeleteCampaignResponse(BaseModel):
    success: bool
    reason: Optional[str] = None

# Helper function to compute campaign status
def compute_campaign_status(campaign: Campaign) -> str:
    current_date = date.today()
    if campaign.start_date > current_date:
        return "Pending"
    elif campaign.start_date <= current_date <= campaign.end_date:
        return "Live"
    else:
        return "Completed"

# Endpoint to create a new campaign
@router.post("/campaigns", response_model=CampaignResponse, tags=["campaigns"])
def create_campaign(
    campaign: CampaignCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verify that the project exists and belongs to the current user
    project = db.query(Project).filter(Project.id == campaign.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate date logic
    if campaign.start_date >= campaign.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    # Create the new campaign without project_name
    new_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        project_id=campaign.project_id,
        requirements=campaign.requirements,
        start_date=campaign.start_date,
        end_date=campaign.end_date
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    
    # Compute status
    computed_status = compute_campaign_status(new_campaign)
    
    return CampaignResponse(
        id=new_campaign.id,
        name=new_campaign.name,
        description=new_campaign.description,
        project_id=new_campaign.project_id,
        project_name=project.name,  # Assign Project Name in response
        requirements=new_campaign.requirements,
        start_date=new_campaign.start_date,
        end_date=new_campaign.end_date,
        computed_status=computed_status
    )

# Endpoint to get a list of all campaigns
@router.get("/campaigns", response_model=List[CampaignResponse], tags=["campaigns"])
def read_campaigns(
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    campaigns = (
        db.query(Campaign)
        .join(Project)
        .filter(Project.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            project_id=campaign.project_id,
            project_name=campaign.project.name,  # Assign Project Name
            requirements=campaign.requirements,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            computed_status=compute_campaign_status(campaign)
        )
        for campaign in campaigns
    ]

# Endpoint to get a specific campaign by ID
@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse, tags=["campaigns"])
def read_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    campaign = (
        db.query(Campaign)
        .join(Project)
        .filter(Campaign.id == campaign_id, Project.user_id == current_user.id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    computed_status = compute_campaign_status(campaign)
    
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        project_id=campaign.project_id,
        project_name=campaign.project.name,  # Assign Project Name
        requirements=campaign.requirements,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        computed_status=computed_status
    )

# Endpoint to delete a campaign
@router.delete("/campaigns/{campaign_id}", response_model=DeleteCampaignResponse, tags=["campaigns"])
def delete_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    campaign = (
        db.query(Campaign)
        .join(Project)
        .filter(Campaign.id == campaign_id, Project.user_id == current_user.id)
        .first()
    )
    if not campaign:
        # Return a JSON response with success=False and a reason
        return DeleteCampaignResponse(success=False, reason="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    # Return a JSON response with success=True
    return DeleteCampaignResponse(success=True)

# Endpoint to update a campaign
@router.put("/campaigns/{campaign_id}", response_model=CampaignUpdateResponse, tags=["campaigns"])
def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve the campaign with associated project
    campaign = (
        db.query(Campaign)
        .join(Project)
        .filter(Campaign.id == campaign_id, Project.user_id == current_user.id)
        .first()
    )
    
    if not campaign:
        # Return failure response
        return CampaignUpdateResponse(success=False, reason="Campaign not found")
    
    # If project_id is being updated, verify the new project exists and belongs to the user
    if campaign_update.project_id is not None and campaign_update.project_id != campaign.project_id:
        new_project = (
            db.query(Project)
            .filter(Project.id == campaign_update.project_id, Project.user_id == current_user.id)
            .first()
        )
        if not new_project:
            # Return failure response
            return CampaignUpdateResponse(success=False, reason="New project not found or does not belong to the user")
    else:
        new_project = campaign.project  # Existing project

    # Update fields if provided
    update_data = campaign_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    # Validate date logic if dates are updated
    if campaign.start_date and campaign.end_date and campaign.start_date >= campaign.end_date:
        return CampaignUpdateResponse(success=False, reason="Start date must be before end date")
    
    # Commit the changes
    db.commit()
    db.refresh(campaign)
    
    # Return success response
    return CampaignUpdateResponse(success=True)