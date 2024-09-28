from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models import Campaign, User, Project
from ..database import get_db
from .auth import get_current_user
from pydantic import BaseModel
from typing import List

# Create a FastAPI router for campaigns
router = APIRouter()

# Pydantic models for request and response validation
class CampaignCreate(BaseModel):
    name: str
    description: str
    project_id: int
    requirements: str
    status: str = "pending"
    start_date: str = None
    end_date: str = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: str
    project_id: int
    requirements: str
    status: str
    start_date: str
    end_date: str

    class Config:
        orm_mode = True

# Endpoint to create a new campaign
@router.post("/campaigns/", response_model=CampaignResponse, tags=["campaigns"])
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == campaign.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        project_id=campaign.project_id,
        requirements=campaign.requirements,
        status=campaign.status,
        start_date=campaign.start_date,
        end_date=campaign.end_date
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign

# Endpoint to get a list of all campaigns
@router.get("/campaigns/", response_model=List[CampaignResponse], tags=["campaigns"])
def read_campaigns(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaigns = db.query(Campaign).join(Project).filter(Project.user_id == current_user.id).offset(skip).limit(limit).all()
    return campaigns

# Endpoint to get a specific campaign by ID
@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse, tags=["campaigns"])
def read_campaign(campaign_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).join(Project).filter(Campaign.id == campaign_id, Project.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

# Endpoint to delete a campaign
@router.delete("/campaigns/{campaign_id}", response_model=CampaignResponse, tags=["campaigns"])
def delete_campaign(campaign_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).join(Project).filter(Campaign.id == campaign_id, Project.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(campaign)
    db.commit()
    return campaign
