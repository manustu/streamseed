# models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Enum,
    TIMESTAMP,
    func,
    UniqueConstraint,
    ForeignKey,
    DateTime,
    Text,
    Date,
    JSON,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    profile_picture_url = Column(String(255))
    registration_date = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(Enum('local', 'google', 'facebook', 'twitter'), default='local')
    social_id = Column(String(255))

    __table_args__ = (
        UniqueConstraint('auth_provider', 'social_id', name='unique_social_provider'),
    )

    # Relationships
    sessions = relationship("Session", back_populates="user")
    projects = relationship("Project", back_populates="user")
    sent_messages = relationship("Message", foreign_keys='Message.sender_id', back_populates="sender")
    received_messages = relationship("Message", foreign_keys='Message.receiver_id', back_populates="receiver")
    notifications = relationship("Notification", back_populates="user")


class Session(Base):
    __tablename__ = "users_sessions"
    
    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    platform = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship to user
    user = relationship("User", back_populates="sessions")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # Removed the status column
    # status = Column(Enum('active', 'inactive', 'completed'), default='active')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationship with campaigns
    campaigns = relationship("Campaign", back_populates="project")

    # Relationship with user
    user = relationship("User", back_populates="projects")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    # Removed the status column
    # status = Column(Enum('pending', 'live', 'completed'), default='pending')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="campaigns")
    campaign_creators = relationship("CampaignCreator", back_populates="campaign")
    analytics = relationship("CampaignAnalytics", back_populates="campaign")


class Creator(Base):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bio = Column(Text)
    social_links = Column(JSON)
    rating = Column(Float, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships with campaign_creators
    campaign_creators = relationship("CampaignCreator", back_populates="creator")


class CampaignCreator(Base):
    __tablename__ = "campaign_creators"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    status = Column(Enum('invited', 'accepted', 'rejected'), default='invited')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_creators")
    creator = relationship("Creator", back_populates="campaign_creators")


class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    metric_type = Column(String(255), nullable=False)
    value = Column(Integer, nullable=False)
    recorded_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship
    campaign = relationship("Campaign", back_populates="analytics")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum('read', 'unread'), default='unread')
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum('read', 'unread'), default='unread')
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="notifications")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    campaign = relationship("Campaign")
    creator = relationship("Creator")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
