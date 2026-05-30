import json
import logging
import pandas as pd
from ai_engine.agents import get_llm, ATTENDANCE_PROMPT

logger = logging.getLogger(__name__)

def process_excel_data(file_path: str) -> list[dict]:
    """
    Reads an Excel file containing attendance data.
    Expected columns (or similar): 'Employee Name', 'Login Time', 'Logout Time'.
    Calculates total hours and number of leaves per employee.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # We need to find the correct columns, doing a fuzzy match or expecting standard names
        # Standardize column names for easier access (lower case, strip spaces)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Try to identify the key columns
        # Prioritize columns with 'name', avoid 'id' if 'employee' is used as a fallback
        name_col = next((c for c in df.columns if 'name' in c), None)
        if not name_col:
            name_col = next((c for c in df.columns if 'employee' in c and 'id' not in c), None)
        if not name_col:
            name_col = next((c for c in df.columns if 'employee' in c or 'emp' in c), None)
            
        login_col = next((c for c in df.columns if 'in' in c or 'start' in c), None)
        logout_col = next((c for c in df.columns if 'out' in c or 'end' in c), None)
        
        if not name_col:
            raise ValueError("Could not identify an 'Employee Name' column in the uploaded file.")
            
        # Grouping by employee
        grouped = df.groupby(name_col)
        
        results = []
        for name, group in grouped:
            total_hours = 0.0
            leaves_taken = 0
            
            for _, row in group.iterrows():
                # Check if login/logout exist
                login_val = row[login_col] if login_col else pd.NaT
                logout_val = row[logout_col] if logout_col else pd.NaT
                
                # If both are missing or NaT, count as leave
                if pd.isna(login_val) and pd.isna(logout_val):
                    leaves_taken += 1
                else:
                    # Try to calculate hours if we have valid datetime/time objects
                    try:
                        # Ensure they are datetime objects
                        if isinstance(login_val, str):
                            login_val = pd.to_datetime(login_val)
                        if isinstance(logout_val, str):
                            logout_val = pd.to_datetime(logout_val)
                            
                        # If it's just time, we can combine with today to get a delta
                        # If it's datetime, direct subtraction works
                        if hasattr(login_val, 'hour') and hasattr(logout_val, 'hour'):
                            # Simple hour calculation if they are just datetime.time
                            if type(login_val) != pd.Timestamp:
                                login_val = pd.to_datetime(str(login_val))
                            if type(logout_val) != pd.Timestamp:
                                logout_val = pd.to_datetime(str(logout_val))
                                
                            delta = logout_val - login_val
                            hours = delta.total_seconds() / 3600.0
                            if hours < 0: # Crossed midnight
                                hours += 24
                            total_hours += hours
                    except Exception as e:
                        logger.warning(f"Error calculating hours for {name}: {e}")
            
            results.append({
                "name": str(name),
                "total_hours": round(total_hours, 1),
                "leaves_taken": leaves_taken
            })
            
        return results
        
    except Exception as e:
        logger.error(f"Error processing Excel data: {e}")
        raise

def generate_attendance_report(file_path: str) -> list[dict]:
    """
    Processes the Excel file and passes the summarized data to the LLM 
    to generate performance scores and feedback.
    """
    try:
        # 1. Extract and summarize data with Pandas
        raw_data = process_excel_data(file_path)
        
        # 2. Format for LLM
        data_str = json.dumps(raw_data, indent=2)
        
        # 3. Call LLM
        llm = get_llm(temperature=0.2)
        chain = ATTENDANCE_PROMPT | llm
        response = chain.invoke({"attendance_data": data_str})
        
        # 4. Parse JSON response
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.strip("`").replace("json\n", "", 1)
        
        report_data = json.loads(content)
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {e}")
        # Return raw data as fallback if LLM fails, adding placeholder score/feedback
        fallback = []
        try:
            raw_data = process_excel_data(file_path)
            for item in raw_data:
                item['ai_score'] = 'N/A'
                item['ai_feedback'] = f"Error generating feedback: {str(e)}"
                fallback.append(item)
            return fallback
        except:
            raise
