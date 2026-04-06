import yaml
import os
from core.db_client import DBClient
from core.models import TestPlan, TestStep

db = DBClient()
session = db.get_session()

def migrate():
    source_dir = "data/test_plans/approved"
    if not os.path.exists(source_dir):
        print("❌ No approved YAMLs found to migrate.")
        return

    for f_name in os.listdir(source_dir):
        if not f_name.endswith(".yaml"): continue
        
        with open(os.path.join(source_dir, f_name), 'r') as f:
            data = yaml.safe_load(f)
            
            # Prevent duplicates
            if session.query(TestPlan).filter_by(title=data['title']).first():
                print(f"⏩ Skipping {data['title']} (Already exists)")
                continue

            plan = TestPlan(title=data['title'], status="approved")
            for i, s in enumerate(data['steps']):
                plan.steps.append(TestStep(
                    action=s['action'],
                    selector=s.get('selector'),
                    data=s.get('data'),
                    sequence=i
                ))
            session.add(plan)
            print(f"✅ Migrated: {data['title']}")

    session.commit()
    session.close()

if __name__ == "__main__":
    migrate()