from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from core.db_client import DBClient
# Added TestResult to the import list below:
from core.models import TestPlan, TestStep, TestResult 
from api.schemas import PlanCreate, PlanRead, ResultCreate, ResultRead, StepsUpdate
from typing import List

app = FastAPI(title="Sentinel-QA API")
db_client = DBClient()

def get_db():
    db = db_client.get_session()
    try: yield db
    finally: db.close()

@app.get("/plans", response_model=List[PlanRead])
def get_plans(status: str = "approved", db: Session = Depends(get_db)):
    return db.query(TestPlan).filter_by(status=status).all()

@app.post("/plans", response_model=PlanRead)
def create_plan(plan_data: PlanCreate, db: Session = Depends(get_db)):
    plan = TestPlan(title=plan_data.title, status="pending")
    for i, s in enumerate(plan_data.steps):
        # 1. Convert Pydantic object to dict
        step_dict = s.model_dump()
        # 2. Remove the 'sequence' key if it exists in the dict
        step_dict.pop('sequence', None)
        # 3. Create the DB record with the loop counter 'i' as the sequence
        plan.steps.append(TestStep(**step_dict, sequence=i))
        
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@app.patch("/plans/{plan_id}/approve", response_model=PlanRead)
def approve_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TestPlan).get(plan_id)
    if plan:
        plan.status = "approved"
        db.commit()
        db.refresh(plan)
    return plan

# --- RESULT LOGGING ---
@app.post("/results", response_model=ResultRead)
def log_result(res: ResultCreate, db: Session = Depends(get_db)):
    result = TestResult(**res.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

@app.get("/results/history/{selector}", response_model=List[ResultRead])
def get_selector_history(selector: str, db: Session = Depends(get_db)):
    """Used by AI to find previous failures for a specific selector."""
    return db.query(TestResult).filter(TestResult.failing_selector == selector).all()

# --- MANAGEMENT (SWAGGER DELETE) ---
@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TestPlan).get(plan_id)
    if not plan:
        return {"error": "Not found"}
    db.delete(plan)
    db.commit()
    return {"status": f"Deleted plan {plan_id}"}
@app.put("/plans/{plan_id}/steps", response_model=PlanRead)
def update_steps(plan_id: int, body: StepsUpdate, db: Session = Depends(get_db)):
    """Saves human-edited steps from Streamlit back to DB."""
    plan = db.query(TestPlan).get(plan_id)
    if not plan:
        return {"error": "Not found"}
    for step in plan.steps:
        db.delete(step)
    for i, s in enumerate(body.steps):
        step_dict = s.model_dump()
        step_dict.pop('sequence', None)
        plan.steps.append(TestStep(**step_dict, sequence=i))
    db.commit()
    db.refresh(plan)
    return plan

@app.patch("/plans/{plan_id}/claim", response_model=PlanRead)
def claim_plan(plan_id: int, worker_id: str, db: Session = Depends(get_db)):
    """xdist worker claims a test to prevent parallel collision."""
    plan = db.query(TestPlan).get(plan_id)
    if plan and not plan.claimed_by:
        plan.claimed_by = worker_id
        plan.status = "running"
        db.commit()
        db.refresh(plan)
    return plan
