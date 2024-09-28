import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..models import User
from ..database import get_db
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from ..config.settings import OAUTH_PROVIDERS
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# Secret key and JWT configuration
SECRET_KEY = "your_secret_key_here"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
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

# Register new users
@router.post("/register", tags=["auth"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_password = pwd_context.hash(user.password)
    
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        auth_provider="local"  # Default or as per your logic
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

# Login and generate JWT token
@router.post("/token", tags=["auth"])
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return RedirectResponse(url=f'/?token={access_token}')
