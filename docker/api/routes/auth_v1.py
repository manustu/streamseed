import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..models import User, Session as SessionModel
from ..database import get_db
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from ..config.settings import OAUTH_PROVIDERS
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    session = db.query(SessionModel).filter(SessionModel.session_token == token).first()
    if session is None or session.expires_at < datetime.utcnow():
        raise credentials_exception
    
    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

# Initialize OAuth
oauth = OAuth()

# Register each OAuth provider
for name, details in OAUTH_PROVIDERS.items():
    oauth.register(
        name=name,
        client_id=details['client_id'],
        client_secret=details['client_secret'],
        authorize_url=details['authorize_url'],
        access_token_url=details['access_token_url'],
        redirect_uri=details['redirect_uri'],
        client_kwargs={'scope': details['scope']}
    )

# Pydantic model for registration
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

# Pydantic model for login
class UserLogin(BaseModel):
    email: str
    password: str
    platform: str

@router.post("/register", tags=["auth"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    
    # Create a new user instance
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        auth_provider="local"  # Default or as per your logic
    )
    
    # Add the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login", tags=["auth"])
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # Check if the user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if not existing_user:
        raise HTTPException(status_code=400, detail="User does not exist.")

    # Verify the password
    if not pwd_context.verify(user.password, existing_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password.")
    
    # Generate a unique session token
    session_token = secrets.token_urlsafe(32)
    
    # Create a session with an expiration time, for example 24 hours
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    new_session = SessionModel(
        user_id=existing_user.id,
        session_token=session_token,
        expires_at=expires_at,
        platform=user.platform
    )
    
    # Add the session to the database
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {"message": "Login successful", "session_token": session_token}

# OAuth login route
@router.get('/auth/{provider}', tags=["auth"])
async def oauth_login(request: Request, provider: str):
    redirect_uri = request.url_for(f'{provider}_callback')
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

# OAuth callback route
@router.route('/auth/{provider}/callback')
async def oauth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    user_info = await client.userinfo()

    user = db.query(User).filter(User.social_id == user_info['id'], User.auth_provider == provider).first()

    if not user:
        user = User(
            email=user_info.get('email'),
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            auth_provider=provider,
            social_id=user_info['id'],
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate a unique session token
    session_token = secrets.token_urlsafe(32)
    
    # Create a session with an expiration time, for example 24 hours
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    new_session = SessionModel(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at,
        platform=provider
    )
    
    # Add the session to the database
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return RedirectResponse(url=f'/?token={session_token}')

