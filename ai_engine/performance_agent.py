import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ai_engine.agents import get_llm

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Define the Structured Output Schema
# ──────────────────────────────────────────────────────────────────────────────

class PerformanceReviewResult(BaseModel):
    """Structured output expected from the LLM for a performance review."""
    performance_score: int = Field(
        description="Overall performance score from 0 to 100 based on all provided metrics."
    )
    kpi_achievement_percent: float = Field(
        description="Calculated KPI achievement percentage from 0.0 to 100.0."
    )
    strengths: List[str] = Field(
        description="List of the employee's key strengths identified from the data."
    )
    areas_for_improvement: List[str] = Field(
        description="List of specific areas where the employee can improve."
    )
    recommended_actions: List[str] = Field(
        description="List of actionable recommendations for the employee's growth."
    )

# ──────────────────────────────────────────────────────────────────────────────
# 2. Define the Prompt Template
# ──────────────────────────────────────────────────────────────────────────────

parser = PydanticOutputParser(pydantic_object=PerformanceReviewResult)

PERFORMANCE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an Expert HR Analyst and Performance Reviewer.\n"
        "Your task is to generate a comprehensive, structured performance review based on the provided employee data.\n"
        "Be objective, professional, and base your analysis strictly on the provided data.\n\n"
        "{format_instructions}\n"
    ),
    (
        "human",
        "Employee Profile Data:\n"
        "Name: {employee_name}\n"
        "Department: {department}\n"
        "Attendance Score: {attendance_score}/100\n\n"
        "Employee Specific Performance Data:\n"
        "{row_data}\n"
    )
])

# ──────────────────────────────────────────────────────────────────────────────
# 3. Execution Function
# ──────────────────────────────────────────────────────────────────────────────

def generate_performance_review(employee_profile, row_data: str) -> dict:
    """
    Invokes the LLM using structured output to generate a performance review.
    Returns a dictionary of the extracted fields.
    """
    try:
        llm = get_llm(temperature=0.2)
        
        chain = PERFORMANCE_PROMPT | llm | parser
        
        result: PerformanceReviewResult = chain.invoke({
            "employee_name": employee_profile.user.username,
            "department": employee_profile.department,
            "attendance_score": employee_profile.attendance_score,
            "row_data": row_data,
            "format_instructions": parser.get_format_instructions()
        })
        
        # Convert list of strings to newline-separated strings for the TextField storage
        return {
            "performance_score": result.performance_score,
            "kpi_achievement_percent": result.kpi_achievement_percent,
            "strengths": "\n".join(f"- {s}" for s in result.strengths),
            "areas_for_improvement": "\n".join(f"- {a}" for a in result.areas_for_improvement),
            "recommended_actions": "\n".join(f"- {r}" for r in result.recommended_actions),
        }
        
    except Exception as e:
        logger.exception("Failed to generate performance review via LLM.")
        raise RuntimeError(f"Performance Review Agent Error: {e}")
