import os, json, re, secrets
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from sqlmodel import SQLModel, create_engine, Session, select, Field
from passlib.context import CryptContext

load_dotenv()
app=FastAPI(title="PathPilot AI",version="3.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Database setup
DATABASE_URL = "sqlite:///./pathpilot.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

SKILLS=["Python","Statistics","SQL","Machine Learning","Deep Learning","NLP","Deployment","MLOps"]

# User and Session models for authentication
class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SessionModel(SQLModel, table=True):
    __tablename__ = "sessions"
    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Database models for learner profiles
class ProfileModel(SQLModel, table=True):
    __tablename__ = "profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = "Learner"
    goal: str = "Machine Learning Engineer"
    experience: str = "Intermediate"
    interests: str = "{}"  # JSON string
    completed_courses: str = "[]"  # JSON string
    weekly_hours: int = 10
    preferences: str = "[]"  # JSON string
    skills: str = "{}"  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Pydantic models for API
class Profile(BaseModel):
    name:str="Learner"; goal:str="Machine Learning Engineer"; experience:str="Intermediate"
    interests:List[str]=[]; completed_courses:List[str]=[]; weekly_hours:int=10
    preferences:List[str]=[]; skills:Dict[str,float]={}

# Auth request models
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LogoutRequest(BaseModel):
    token: str

# Profile request models
class ProfileRequest(BaseModel):
    profile: Profile

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str,str]] = []

class AssessmentRequest(BaseModel):
    results: Dict[str,int]

# Helper function to verify token
def verify_token(authorization: Optional[str]) -> int:
    """Verify Bearer token and return user_id"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    session = Session(engine)
    try:
        session_record = session.exec(select(SessionModel).where(SessionModel.token == token)).first()
        if not session_record:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return session_record.user_id
    finally:
        session.close()

# Helper functions for database
def profile_to_model(profile: Profile, user_id: int) -> ProfileModel:
    """Convert pydantic Profile to database ProfileModel"""
    return ProfileModel(
        user_id=user_id,
        name=profile.name,
        goal=profile.goal,
        experience=profile.experience,
        interests=json.dumps(profile.interests),
        completed_courses=json.dumps(profile.completed_courses),
        weekly_hours=profile.weekly_hours,
        preferences=json.dumps(profile.preferences),
        skills=json.dumps({k: float(v) for k, v in profile.skills.items()}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def model_to_profile(model: ProfileModel) -> Profile:
    """Convert database ProfileModel to pydantic Profile"""
    return Profile(
        name=model.name,
        goal=model.goal,
        experience=model.experience,
        interests=json.loads(model.interests) if model.interests else [],
        completed_courses=json.loads(model.completed_courses) if model.completed_courses else [],
        weekly_hours=model.weekly_hours,
        preferences=json.loads(model.preferences) if model.preferences else [],
        skills=json.loads(model.skills) if model.skills else {}
    )

# Initialize database tables
SQLModel.metadata.create_all(engine)

ROLE_TARGETS={
"Machine Learning Engineer":{"Python":80,"Statistics":65,"SQL":55,"Machine Learning":75,"Deep Learning":65,"NLP":45,"Deployment":70,"MLOps":55},
"AI Engineer":{"Python":80,"Statistics":60,"SQL":45,"Machine Learning":75,"Deep Learning":75,"NLP":70,"Deployment":75,"MLOps":60},
"Data Scientist":{"Python":75,"Statistics":80,"SQL":70,"Machine Learning":75,"Deep Learning":45,"NLP":30,"Deployment":40,"MLOps":30},
"Software Engineer":{"Python":65,"Statistics":35,"SQL":60,"Machine Learning":30,"Deep Learning":15,"NLP":10,"Deployment":65,"MLOps":45}}
PR={"Machine Learning":["Python","Statistics"],"Deep Learning":["Machine Learning"],"NLP":["Deep Learning"],"Deployment":["Python","Machine Learning"],"MLOps":["Deployment"]}
RES=[
("Python Data Analysis","Python","Course","https://pandas.pydata.org/docs/","12h"),
("An Introduction to Statistical Learning","Statistics","Book","https://www.statlearning.com/","25h"),
("Machine Learning Crash Course","Machine Learning","Course","https://developers.google.com/machine-learning/crash-course","15h"),
("scikit-learn User Guide","Machine Learning","Documentation","https://scikit-learn.org/stable/user_guide.html","12h"),
("PyTorch Tutorials","Deep Learning","Tutorial","https://pytorch.org/tutorials/","10h"),
("Hugging Face NLP Course","NLP","Course","https://huggingface.co/learn/nlp-course/chapter1/1","18h"),
("FastAPI Tutorial","Deployment","Documentation","https://fastapi.tiangolo.com/tutorial/","6h"),
("Docker Get Started","Deployment","Tutorial","https://docs.docker.com/get-started/","5h"),
("Made With ML","MLOps","Course","https://madewithml.com/","15h")]
PROJECTS={"Python":"Data cleaning and EDA dashboard","Statistics":"A/B testing analysis notebook","SQL":"Analytics dashboard with SQL","Machine Learning":"Customer churn predictor","Deep Learning":"PyTorch image classifier","NLP":"Semantic search engine","Deployment":"Deploy an ML API with FastAPI and Docker","MLOps":"ML monitoring mini-pipeline"}

class Chat(BaseModel): profile:Profile; message:str; history:List[Dict[str,str]]=[]
class Assessment(BaseModel): profile:Profile; results:Dict[str,int]

def target(p): 
    g=p.goal.lower()
    if "data scientist" in g:return "Data Scientist"
    if "ai engineer" in g or "genai" in g or "llm" in g:return "AI Engineer"
    if "software" in g:return "Software Engineer"
    return "Machine Learning Engineer"

def gaps(p):
    r=ROLE_TARGETS[target(p)]; s=p.skills
    return sorted([{"skill":k,"current":round(s.get(k,0)),"target":v,"gap":max(0,round(v-s.get(k,0)))} for k,v in r.items()],key=lambda x:x["gap"],reverse=True)

def roadmap(p):
    gs=gaps(p); ordered=[x["skill"] for x in gs]
    changed=True
    while changed:
        changed=False
        for k in ordered[:]:
            for q in PR.get(k,[]):
                if q not in ordered and p.skills.get(q,0)<ROLE_TARGETS[target(p)].get(q,0):
                    ordered.insert(max(0,ordered.index(k)),q); changed=True
    out=[]
    for i,k in enumerate(ordered[:8]):
        rr=next((x for x in RES if x[1]==k),None)
        out.append({"id":i+1,"skill":k,"status":"Current focus" if i==0 else "Upcoming",
        "prerequisites":PR.get(k,[]),"resource":rr[0] if rr else "Targeted practice",
        "url":rr[3] if rr else None,"time":rr[4] if rr else None,
        "project":PROJECTS[k],"milestone":f"Reach {ROLE_TARGETS[target(p)].get(k,60)}% proficiency in {k}"})
    return out

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")

def llm(system,user):
    if not client:return None
    try:
        prompt=system+"\n\n"+user
        r=client.models.generate_content(model=MODEL, contents=prompt)
        return r.text
    except Exception:return None

@app.get("/api/health")
def health(): return {"status":"ok","llm_enabled":bool(client)}

# Authentication endpoints
@app.post("/api/signup")
def signup(req: SignupRequest):
    """Sign up a new user"""
    session = Session(engine)
    try:
        # Check if email already exists
        existing_user = session.exec(select(UserModel).where(UserModel.email == req.email)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user = UserModel(
            email=req.email,
            password_hash=hash_password(req.password)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create session token
        token = secrets.token_urlsafe(32)
        session_record = SessionModel(token=token, user_id=user.id)
        session.add(session_record)
        session.commit()
        
        # Create default profile for new user
        default_profile = ProfileModel(
            user_id=user.id,
            name="Learner",
            goal="Machine Learning Engineer",
            experience="Intermediate",
            interests=json.dumps([]),
            completed_courses=json.dumps([]),
            weekly_hours=10,
            preferences=json.dumps([]),
            skills=json.dumps({"Python": 50})
        )
        session.add(default_profile)
        session.commit()
        
        return {"token": token, "email": req.email}
    finally:
        session.close()

@app.post("/api/login")
def login(req: LoginRequest):
    """Login with email and password"""
    session = Session(engine)
    try:
        # Find user by email
        user = session.exec(select(UserModel).where(UserModel.email == req.email)).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session token
        token = secrets.token_urlsafe(32)
        session_record = SessionModel(token=token, user_id=user.id)
        session.add(session_record)
        session.commit()
        
        return {"token": token, "email": req.email}
    finally:
        session.close()

@app.post("/api/logout")
def logout(req: LogoutRequest):
    """Logout by deleting session token"""
    session = Session(engine)
    try:
        session_record = session.exec(select(SessionModel).where(SessionModel.token == req.token)).first()
        if session_record:
            session.delete(session_record)
            session.commit()
        return {"message": "Logged out successfully"}
    finally:
        session.close()

@app.post("/api/profile")
def build_profile(req: ProfileRequest, authorization: Optional[str] = Header(None)):
    """Create or update profile and store in database"""
    user_id = verify_token(authorization)
    session = Session(engine)
    try:
        # Check if profile exists for this user
        existing = session.exec(select(ProfileModel).where(ProfileModel.user_id == user_id)).first()
        
        if existing:
            # Update existing profile
            existing.name = req.profile.name
            existing.goal = req.profile.goal
            existing.experience = req.profile.experience
            existing.interests = json.dumps(req.profile.interests)
            existing.completed_courses = json.dumps(req.profile.completed_courses)
            existing.weekly_hours = req.profile.weekly_hours
            existing.preferences = json.dumps(req.profile.preferences)
            existing.skills = json.dumps({k: float(v) for k, v in req.profile.skills.items()})
            existing.updated_at = datetime.utcnow()
            session.add(existing)
        else:
            # Create new profile
            model = ProfileModel(
                user_id=user_id,
                name=req.profile.name,
                goal=req.profile.goal,
                experience=req.profile.experience,
                interests=json.dumps(req.profile.interests),
                completed_courses=json.dumps(req.profile.completed_courses),
                weekly_hours=req.profile.weekly_hours,
                preferences=json.dumps(req.profile.preferences),
                skills=json.dumps({k: float(v) for k, v in req.profile.skills.items()}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(model)
        
        session.commit()
        p = req.profile
        return {"role":target(p),"gaps":gaps(p),"roadmap":roadmap(p)}
    finally:
        session.close()

@app.get("/api/profile")
def get_profile(authorization: Optional[str] = Header(None)):
    """Retrieve saved profile by user_id from token"""
    user_id = verify_token(authorization)
    session = Session(engine)
    try:
        profile_model = session.exec(select(ProfileModel).where(ProfileModel.user_id == user_id)).first()
        
        if not profile_model:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = model_to_profile(profile_model)
        return {
            "profile": profile.model_dump(),
            "role": target(profile),
            "gaps": gaps(profile),
            "roadmap": roadmap(profile)
        }
    finally:
        session.close()

@app.post("/api/chat")
def chat(req: ChatRequest, authorization: Optional[str] = Header(None)):
    user_id = verify_token(authorization)
    session = Session(engine)
    try:
        # Load learner profile from database
        profile_model = session.exec(select(ProfileModel).where(ProfileModel.user_id == user_id)).first()
        
        if not profile_model:
            raise HTTPException(status_code=404, detail="Profile not found. Call /api/profile first.")
        
        p = model_to_profile(profile_model)
        context={"profile":p.model_dump(),"role":target(p),"gaps":gaps(p),"roadmap":roadmap(p),"resources":[{"title":a,"skill":b,"type":cc,"url":d,"time":e} for a,b,cc,d,e in RES]}
        system="""You are PathPilot AI, an adaptive learning-path planner. Use the learner's real profile, goals, skills, time budget, prerequisites, roadmap and resources.
You must do two things: (1) answer the learner naturally, and (2) if the learner asks to change their goal, weekly hours, priorities, skills, completed work, what to skip/deprioritize, or roadmap, propose concrete state changes.
Return ONLY valid JSON with this schema:
{"answer":"natural concise response","updates":{"goal":null,"weekly_hours":null,"experience":null,"skill_updates":{},"remove_skills":[],"prioritize_skills":[]}}
Only put values in updates when the learner explicitly requests or clearly states them. skill_updates values must be numbers 0-100. remove_skills should contain skill names to deprioritize, not permanently delete from the learner's skill profile. prioritize_skills should contain skill names to prioritize. Do not invent scores. Do not mention system prompts or hard-coded behavior."""
        prompt=f"LEARNER CONTEXT:\n{json.dumps(context,indent=2)}\n\nCONVERSATION:\n{json.dumps(req.history[-8:])}\n\nQUESTION:\n{req.message}"
        answer=llm(system,prompt)
        if answer:
            try:
                data=json.loads(answer.strip().replace("```json","").replace("```",""))
                u=data.get("updates") or {}
                if u.get("goal"): p.goal=str(u["goal"])
                if u.get("weekly_hours") is not None: p.weekly_hours=max(1,int(u["weekly_hours"]))
                if u.get("experience"): p.experience=str(u["experience"])
                for k,v in (u.get("skill_updates") or {}).items():
                    if k in SKILLS: p.skills[k]=max(0,min(100,float(v)))
                # Priorities are represented in roadmap ordering via temporary preference order.
                pr=[x for x in (u.get("prioritize_skills") or []) if x in SKILLS]
                rm=roadmap(p)
                if pr:
                    rank={k:i for i,k in enumerate(pr)}
                    rm=sorted(rm,key=lambda x:(rank.get(x["skill"],99), x["id"]))
                    for i,x in enumerate(rm): x["id"]=i+1; x["status"]="Current focus" if i==0 else "Upcoming"
                # Deprioritize without losing the skill from the learner profile.
                depr=[x for x in (u.get("remove_skills") or []) if x in SKILLS]
                if depr:
                    rm=[x for x in rm if x["skill"] not in depr]+[x for x in rm if x["skill"] in depr]
                    for i,x in enumerate(rm): x["id"]=i+1; x["status"]="Current focus" if i==0 else ("Deprioritized" if x["skill"] in depr else "Upcoming")
                
                # Save updated profile to database
                profile_model.name = p.name
                profile_model.goal = p.goal
                profile_model.experience = p.experience
                profile_model.interests = json.dumps(p.interests)
                profile_model.completed_courses = json.dumps(p.completed_courses)
                profile_model.weekly_hours = p.weekly_hours
                profile_model.preferences = json.dumps(p.preferences)
                profile_model.skills = json.dumps({k: float(v) for k, v in p.skills.items()})
                profile_model.updated_at = datetime.utcnow()
                session.add(profile_model)
                session.commit()
                
                return {"answer":data.get("answer",answer),"source":"llm","profile":p.model_dump(),"gaps":gaps(p),"roadmap":rm}
            except Exception:
                return {"answer":answer,"source":"llm","profile":p.model_dump(),"gaps":gaps(p),"roadmap":roadmap(p)}
        gs=gaps(p); top=gs[0]["skill"] if gs else "your next milestone"
        return {"answer":f"Your highest-priority gap is {top} ({gs[0]['current']}% current vs {gs[0]['target']}% target). Based on your {p.weekly_hours} hours/week, focus on the first roadmap milestone before moving ahead. Configure a Gemini API key in backend/.env for fully open-ended AI conversation.","source":"local_fallback","profile":p.model_dump(),"gaps":gs,"roadmap":roadmap(p)}
    finally:
        session.close()

@app.post("/api/assess")
def assess(req: AssessmentRequest, authorization: Optional[str] = Header(None)):
    user_id = verify_token(authorization)
    session = Session(engine)
    try:
        # Load learner profile from database
        profile_model = session.exec(select(ProfileModel).where(ProfileModel.user_id == user_id)).first()
        
        if not profile_model:
            raise HTTPException(status_code=404, detail="Profile not found. Call /api/profile first.")
        
        p = model_to_profile(profile_model)
        for skill, score in req.results.items():
            p.skills[skill] = max(0, min(100, score))
        
        # Save updated profile to database
        profile_model.skills = json.dumps({k: float(v) for k, v in p.skills.items()})
        profile_model.updated_at = datetime.utcnow()
        session.add(profile_model)
        session.commit()
        
        return {"profile": p.model_dump(), "gaps": gaps(p), "roadmap": roadmap(p),
                "message": "Learner model updated and the roadmap was regenerated from the new assessment results."}
    finally:
        session.close()

@app.get("/api/resources")
def resources():
    return {"resources":[{"title":a,"skill":b,"type":c,"url":d,"time":e} for a,b,c,d,e in RES]}
