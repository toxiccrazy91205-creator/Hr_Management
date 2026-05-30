"""
agents.py — LLM initialization and prompt templates for each agent role.

Agents implemented:
 • Screener Agent   — evaluates resumes and returns a shortlist with scores.
 • Scheduler Agent  — assigns interview time-slots to shortlisted candidates.
 • Communicator Agent — drafts personalized follow-up/interview emails.
"""

import os
import logging
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# LLM Factory
# ──────────────────────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance pointed at OpenRouter / NVIDIA NIM.
    Reads configuration from Django settings which in turn read from .env.
    """
    api_key = getattr(settings, "OPENROUTER_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = getattr(settings, "OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

    if not api_key:
        logger.warning(
            "OPENROUTER_API_KEY is not set. LLM calls will fail. "
            "Set it in your .env or environment."
        )

    return ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base=base_url,
        model_name=model,
        temperature=temperature,
        max_tokens=4096,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Prompt Templates
# ──────────────────────────────────────────────────────────────────────────────

SCREENER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert HR Screening Agent. Your job is to evaluate candidate "
        "resumes against a job description and produce a shortlist.\n\n"
        "RULES:\n"
        "1. Evaluate each candidate chunk for relevance to the job description.\n"
        "2. Assign a match_score from 0 to 100.\n"
        "3. Extract the candidate's name and email if visible.\n"
        "4. List the skills that match the required skills.\n"
        "5. Only shortlist candidates with match_score >= 40.\n"
        "6. Return ONLY valid JSON — an array of objects.\n\n"
        "Output format (JSON array):\n"
        "[\n"
        '  {{\n'
        '    "name": "Candidate Name",\n'
        '    "email": "candidate@email.com",\n'
        '    "match_score": 85,\n'
        '    "matched_skills": "Python, Django, REST APIs",\n'
        '    "source_file": "resume.pdf"\n'
        '  }}\n'
        "]\n\n"
        "If no candidates are suitable, return an empty array: []"
    ),
    (
        "human",
        "## Job Details\n"
        "**Title:** {job_title}\n"
        "**Description:** {job_description}\n"
        "**Required Skills:** {required_skills}\n"
        "**Minimum Experience:** {experience_years} years\n\n"
        "## Resume Data Retrieved from Vector DB\n"
        "{resume_chunks}\n\n"
        "Analyze the above resumes and return the shortlisted candidates as a JSON array."
    ),
])


SCHEDULER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an Interview Scheduling Coordinator. Given a list of shortlisted "
        "candidates, assign each one a unique interview time slot.\n\n"
        "RULES:\n"
        "1. Schedule interviews on upcoming weekdays starting from tomorrow.\n"
        "2. Time slots should be between 09:00 and 17:00, each 45 minutes apart.\n"
        "3. Return ONLY valid JSON — an array of objects.\n\n"
        "Output format (JSON array):\n"
        "[\n"
        '  {{\n'
        '    "name": "Candidate Name",\n'
        '    "email": "candidate@email.com",\n'
        '    "interview_slot": "Monday, June 2, 2025 at 10:00 AM"\n'
        '  }}\n'
        "]\n"
    ),
    (
        "human",
        "Shortlisted candidates:\n{candidates_json}\n\n"
        "Assign interview time slots and return the JSON array."
    ),
])


COMMUNICATOR_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Professional HR Communications Agent. Your job is to draft "
        "personalized interview invitation emails for shortlisted candidates.\n\n"
        "RULES:\n"
        "1. Be warm, professional, and concise.\n"
        "2. Include the interview date/time slot in the email body.\n"
        "3. Mention the job title and congratulate them on being shortlisted.\n"
        "4. Include a line asking them to confirm attendance.\n"
        "5. Return ONLY valid JSON — an array of objects.\n\n"
        "Output format (JSON array):\n"
        "[\n"
        '  {{\n'
        '    "name": "Candidate Name",\n'
        '    "email": "candidate@email.com",\n'
        '    "subject": "Interview Invitation — Job Title",\n'
        '    "body": "Full email body text here..."\n'
        '  }}\n'
        "]\n"
    ),
    (
        "human",
        "Job Title: {job_title}\n"
        "Company: Our Company\n\n"
        "Candidates with interview slots:\n{scheduled_json}\n\n"
        "Draft personalized emails for each candidate and return the JSON array."
    ),
])
