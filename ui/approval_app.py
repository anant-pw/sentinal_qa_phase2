import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000/plans"

st.set_page_config(page_title="Sentinel HITL Portal", layout="wide")
st.title("🛡️ Sentinel QA Approval Portal")

# 1. Fetch Pending Plans from API
try:
    response = requests.get(f"{API_URL}?status=pending")
    plans = response.json()
except Exception as e:
    st.error(f"Could not connect to Sentinel API: {e}")
    plans = []

if not plans:
    st.info("No pending test cases in the database.")

for plan in plans:
    with st.expander(f"Review: {plan['title']}"):
        # 2. Extract steps into a format Streamlit Data Editor understands
        steps_df = pd.DataFrame(plan['steps'])
        # Sort by sequence to ensure logical order for the human reviewer
        steps_df = steps_df.sort_values("sequence")[['action', 'selector', 'data']]
        
        edited_steps = st.data_editor(steps_df, key=f"editor_{plan['id']}", num_rows="dynamic")
        
        if st.button("Approve & Sync to DB", key=f"btn_{plan['id']}"):
            # Save edited steps back to DB first
            steps_payload = edited_steps.to_dict(orient='records')
            requests.put(f"{API_URL}/{plan['id']}/steps", json=steps_payload)
            patch_res = requests.patch(f"{API_URL}/{plan['id']}/approve")
            if patch_res.status_code == 200:
                st.success(f"✅ Plan '{plan['title']}' approved!")
                st.rerun()
            else:
                st.error("Failed to approve plan.")