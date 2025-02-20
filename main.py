from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Request
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User
from schemas import UserCreate, UserResponse
from typing import List
from passlib.context import CryptContext
from schemas import UserLogin
from auth import verify_password
from auth import hash_password
from auth import create_access_token, create_refresh_token
from datetime import timedelta 
from auth import get_current_user
from auth import oauth2_scheme
from auth import verify_refresh_token
from pydantic import BaseModel
from models import RefreshToken
from schemas import MalariaReportCreate, MalariaRiskResponse
from fastapi.middleware.cors import CORSMiddleware
from models import MalariaReport
import re


app = FastAPI()

Base.metadata.create_all(bind=engine)



origins = [
    "http://localhost:5173", 
    "https://tectaria-backend.onrender.com"  
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/auth/me")
async def auth_me():
    return {"message": "CORS is working!"}



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/login/")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(db=db, data={"sub": user.email, "user_id": user.id}, )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    

@app.get("/check-name/{name}")
def check_name_availability(name: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.name == name).first()

    if existing_user:  
        return {"available": False, "message": "Name already taken"}

    return {"available": True, "message": "Name is available"}

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(name=user.name, email=user.email, password=hashed_password, latitude=user.latitude, longitude=user.longitude)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/{user_id}", response_model=List[UserResponse])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
        return user
    
@app.get("/users/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/users/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(User).all()


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/debug-token")
def debug_token(token: str = Depends(oauth2_scheme)):
    return {"recieved_token": token}

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@app.get("/malaria-risk/", response_model=MalariaRiskResponse)
def get_malaria_risk(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

    
    nearby_reports = db.query(MalariaReport).filter(
        (MalariaReport.latitude.between(current_user.latitude - 0.1, current_user.latitude + 0.1)) &
        (MalariaReport.longitude.between(current_user.longitude - 0.1, current_user.longitude + 0.1))
    ).all()

    total_cases = sum(report.cases_reported for report in nearby_reports)

   
    if total_cases > 20:
        risk_level = "high"
        color = "red"
    elif total_cases > 5:
        risk_level = "moderate"
        color = "yellow"
    else:
        risk_level = "low"
        color = "green"

    return {"risk_level": risk_level, "color": color}

@app.get("/malaria-risk-map/")
def get_malaria_risk_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

   
    nearby_reports = db.query(MalariaReport).filter(
        (MalariaReport.latitude.between(current_user.latitude - 0.5, current_user.latitude + 0.5)) &
        (MalariaReport.longitude.between(current_user.longitude - 0.5, current_user.longitude + 0.5))
    ).all()

  
    risk_data = []
    for report in nearby_reports:
        total_cases = report.cases_reported

       
        if total_cases > 20:
            risk_level = "high"
            color = "red"
        elif total_cases > 5:
            risk_level = "moderate"
            color = "yellow"
        else:
            risk_level = "low"
            color = "green"

        risk_data.append({
            "latitude": report.latitude,
            "longitude": report.longitude,
            "risk_level": risk_level,
            "color": color
        })

    return {"risk_zones": risk_data}

@app.post("/refresh/")
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    email = verify_refresh_token(request.refresh_token, db)
    new_access_token = create_access_token(data={"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}

@app.post("/logout/")
def logout(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    db.query(RefreshToken).filter(RefreshToken.token == request.refresh_token).delete()
    db.commit()
    return {"message": "Successfully logged out"}


@app.post("/report-malaria/")
def report_malaria(report: MalariaReportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

    new_report = MalariaReport(
        user_id=current_user.id,
        latitude=current_user.latitude,  
        longitude=current_user.longitude,
        cases_reported=report.cases_reported
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {"message": "Malaria report submitted successfully"}



@app.put("/update-location/")
def update_location(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    
    data = request.json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and Longitude are required")

    current_user.latitude = latitude
    current_user.longitude = longitude
    db.commit()
    db.refresh(current_user)

    return {"message": "Location updated automatically"}


@app.get("/")
def read_root():
    return {"message": "MedInnovate API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

