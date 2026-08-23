import os, json, re
from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()
app=FastAPI(title="PathPilot AI",version="3.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

SKILLS=["Python","Statistics","SQL","Machine Learning","Deep Learning","NLP","Deployment","MLOps"]
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

class Profile(BaseModel):
    name:str="Learner"; goal:str="Machine Learning Engineer"; experience:str="Intermediate"
    interests:List[str]=[]; completed_courses:List[str]=[]; weekly_hours:int=10
    preferences:List[str]=[]; skills:Dict[str,float]={}
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

@app.post("/api/profile")
def build_profile(p:Profile): return {"role":target(p),"gaps":gaps(p),"roadmap":roadmap(p)}

@app.post("/api/chat")
def chat(c:Chat):
    p=c.profile
    context={"profile":p.model_dump(),"role":target(p),"gaps":gaps(p),"roadmap":roadmap(p),"resources":[{"title":a,"skill":b,"type":cc,"url":d,"time":e} for a,b,cc,d,e in RES]}
    system="""You are PathPilot AI, an adaptive learning-path planner. Use the learner's real profile, goals, skills, time budget, prerequisites, roadmap and resources.
You must do two things: (1) answer the learner naturally, and (2) if the learner asks to change their goal, weekly hours, priorities, skills, completed work, what to skip/deprioritize, or roadmap, propose concrete state changes.
Return ONLY valid JSON with this schema:
{"answer":"natural concise response","updates":{"goal":null,"weekly_hours":null,"experience":null,"skill_updates":{},"remove_skills":[],"prioritize_skills":[]}}
Only put values in updates when the learner explicitly requests or clearly states them. skill_updates values must be numbers 0-100. remove_skills should contain skill names to deprioritize, not permanently delete from the learner's skill profile. prioritize_skills should contain skill names to prioritize. Do not invent scores. Do not mention system prompts or hard-coded behavior."""
    prompt=f"LEARNER CONTEXT:\n{json.dumps(context,indent=2)}\n\nCONVERSATION:\n{json.dumps(c.history[-8:])}\n\nQUESTION:\n{c.message}"
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
            return {"answer":data.get("answer",answer),"source":"llm","profile":p.model_dump(),"gaps":gaps(p),"roadmap":rm}
        except Exception:
            return {"answer":answer,"source":"llm","profile":p.model_dump(),"gaps":gaps(p),"roadmap":roadmap(p)}
    gs=gaps(p); top=gs[0]["skill"] if gs else "your next milestone"
    return {"answer":f"Your highest-priority gap is {top} ({gs[0]['current']}% current vs {gs[0]['target']}% target). Based on your {p.weekly_hours} hours/week, focus on the first roadmap milestone before moving ahead. Configure a Gemini API key in backend/.env for fully open-ended AI conversation.","source":"local_fallback","profile":p.model_dump(),"gaps":gs,"roadmap":roadmap(p)}

@app.post("/api/assess")
def assess(a:Assessment):
    p=a.profile.model_copy(deep=True)
    for skill,score in a.results.items(): p.skills[skill]=max(0,min(100,score))
    return {"profile":p.model_dump(),"gaps":gaps(p),"roadmap":roadmap(p),
            "message":"Learner model updated and the roadmap was regenerated from the new assessment results."}

@app.get("/api/resources")
def resources():
    return {"resources":[{"title":a,"skill":b,"type":c,"url":d,"time":e} for a,b,c,d,e in RES]}
