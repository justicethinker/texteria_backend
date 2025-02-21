from fastapi import FastAPI, Depends, APIRouter, HTTPException, status
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
from dotenv import load_dotenv
import requests
import os
import re


app = FastAPI()

Base.metadata.create_all(bind=engine)

load_dotenv()

HERE_API_KEY = os.getenv("HERE_API_KEY")

if not HERE_API_KEY:
    raise ValueError("HERE_API_KEY is missing! Add it to your .env file or environment variables.")



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
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        latitude=user.latitude,  
        longitude=user.longitude  
    )

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

import requests

AI_API_URL = "https://2949bcd3-2f94-4f33-8fd2-848fe9144150-00-2clainn87cmnh.spock.replit.dev/"  

@app.get("/malaria-risk-map/")
def get_malaria_risk_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

    
    ai_response = requests.post(AI_API_URL, json={
        "latitude": current_user.latitude,
        "longitude": current_user.longitude
    })

    if ai_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch risk analysis from AI")

    ai_data = ai_response.json()  

    
    risk_color_map = {
        "High": "red",
        "Medium": "yellow",
        "Low": "green"
    }
    risk_level = ai_data["risk_level"]
    color = risk_color_map.get(risk_level, "gray")  

    return {
        "latitude": current_user.latitude,
        "longitude": current_user.longitude,
        "risk_level": risk_level,
        "color": color
    }

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
def report_malaria(
    report: MalariaReportCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

   
    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={current_user.latitude},{current_user.longitude}&apiKey={HERE_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch location details")

    data = response.json()

    if "items" not in data or not data["items"]:
        raise HTTPException(status_code=404, detail="Location details not found")

    address = data["items"][0]["address"].get("label", "Unknown Location")

   
    new_report = MalariaReport(
        user_id=current_user.id,
        latitude=current_user.latitude,  
        longitude=current_user.longitude,
        address=address, 
        cases_reported=report.cases_reported,
        risk_level=report.risk_level  
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "message": "Malaria report submitted successfully",
        "location": address,
        "risk_level": report.risk_level
    }


@app.put("/update-location/")
async def update_location(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    data = await request.json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and Longitude are required")

    
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in database")

   
    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={latitude},{longitude}&apiKey={HERE_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch location details")

    data = response.json()

    if "items" not in data or not data["items"]:
        raise HTTPException(status_code=404, detail="Location details not found")

    address_details = data["items"][0]["address"]
    full_address = address_details.get("label", "Unknown Location")

   
    db_user.latitude = latitude
    db_user.longitude = longitude
    db_user.address = full_address  

    db.commit()
    db.refresh(db_user) 

    return {
        "message": "Location updated automatically",
        "latitude": latitude,
        "longitude": longitude,
        "address": full_address
    }


@app.get("/me/")
def get_current_user_info(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="Location data is missing for this user")

  
    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={current_user.latitude},{current_user.longitude}&apiKey={HERE_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch location details")

    data = response.json()

    if "items" not in data or not data["items"]:
        raise HTTPException(status_code=404, detail="Location details not found")

    address_details = data["items"][0]["address"]

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "latitude": current_user.latitude,
        "longitude": current_user.longitude,
        "address": address_details.get("label", "Unknown Location"), 
        "city": address_details.get("city", "Unknown City"),
        "state": address_details.get("state", "Unknown State"),
        "country": address_details.get("countryName", "Unknown Country")
    }




@app.get("/reverse-geocode/")
def reverse_geocode(latitude: float, longitude: float):
    if not HERE_API_KEY:
        raise HTTPException(status_code=500, detail="HERE Maps API key is missing")

    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={latitude},{longitude}&apiKey={HERE_API_KEY}"

    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch location data")

    data = response.json()

    if "items" not in data or not data["items"]:
        raise HTTPException(status_code=404, detail="Location not found")

    return {"address": data["items"][0]["address"]["label"]}


@app.get("/me/", response_model=UserResponse)
def get_current_user_info(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
   
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        latitude=current_user.latitude,
        longitude=current_user.longitude
    )


@app.get("/")
def read_root():
    return {"message": "MedInnovate API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

