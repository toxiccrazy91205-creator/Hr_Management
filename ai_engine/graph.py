"""
graph.py — LangGraph state machine for the HR recruitment agentic workflow.

Workflow nodes:
  1. ingest_resumes  — extract text from uploaded files, store in ChromaDB
  2. screen_candidates — RAG retrieval + Screener Agent LLM call
  3. schedule_interviews — Scheduler Agent assigns time slots
  4. draft_emails — Communicator Agent drafts personalised emails
  5. send_emails — dispatches emails via Django send_mail
                   (runs automatically, no human-in-the-loop pause)
"""

import json
import logging
from typing import TypedDict, List, Dict, Any, Optional, Annotated

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ai_engine.vector_store import add_documents, similarity_search
from ai_engine.agents import (
    get_llm,
    SCREENER_PROMPT,
    SCHEDULER_PROMPT,
    COMMUNICATOR_PROMPT,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# State Schema
# ──────────────────────────────────────────────────────────────────────────────

class HRState(TypedDict, total=False):
    """Typed state flowing through the LangGraph."""
    # Inputs
    job_id: str
    job_title: str
    job_description: str
    required_skills: str
    experience_years: int
    uploaded_file_paths: List[str]

    # Intermediate / outputs
    ingested_docs: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    shortlisted_candidates: List[Dict[str, Any]]
    scheduled_candidates: List[Dict[str, Any]]
    email_drafts: List[Dict[str, Any]]
    emails_sent: bool
    error: Optional[str]


# ──────────────────────────────────────────────────────────────────────────────
# Helper: safe JSON extraction from LLM output
# ──────────────────────────────────────────────────────────────────────────────

def _parse_json_from_llm(text: str) -> list:
    """
    Robustly parse a JSON array from LLM output that may include markdown
    fences or surrounding prose.
    """
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (possibly ```json)
        first_newline = cleaned.index("\n") if "\n" in cleaned else 3
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try to find the JSON array
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        json_str = cleaned[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error: %s\nRaw: %s", exc, json_str[:500])
            return []
    logger.warning("No JSON array found in LLM output: %s", cleaned[:300])
    return []


# ──────────────────────────────────────────────────────────────────────────────
# Node 1: Ingest Resumes
# ──────────────────────────────────────────────────────────────────────────────

def ingest_resumes(state: HRState) -> dict:
    """Extract text from uploaded files and store chunks in ChromaDB."""
    logger.info("▶ Node: ingest_resumes")
    file_paths = state.get("uploaded_file_paths", [])
    job_id = state.get("job_id", "")

    if not file_paths:
        return {"error": "No files uploaded.", "ingested_docs": []}

    try:
        ingested = add_documents(file_paths, job_id=job_id)
        return {"ingested_docs": ingested, "error": None}
    except Exception as exc:
        logger.exception("Ingestion failed")
        return {"error": f"Ingestion error: {exc}", "ingested_docs": []}


# ──────────────────────────────────────────────────────────────────────────────
# Node 2: Screen Candidates (RAG + LLM)
# ──────────────────────────────────────────────────────────────────────────────

def screen_candidates(state: HRState) -> dict:
    """Retrieve relevant chunks from ChromaDB and ask the Screener Agent to shortlist."""
    logger.info("▶ Node: screen_candidates")

    job_id = state.get("job_id", "")
    job_title = state.get("job_title", "")
    job_description = state.get("job_description", "")
    required_skills = state.get("required_skills", "")
    experience_years = state.get("experience_years", 0)

    # Build a combined query for RAG retrieval
    query = f"{job_title} {job_description} {required_skills}"
    chunks = similarity_search(query, n_results=30, job_id=job_id)

    if not chunks:
        return {
            "shortlisted_candidates": [],
            "retrieved_chunks": [],
            "error": "No matching resume chunks found in the vector store.",
        }

    # Format chunks for the prompt
    formatted_chunks = []
    for i, c in enumerate(chunks):
        meta = c.get("metadata", {})
        formatted_chunks.append(
            f"--- Resume Chunk {i + 1} (source: {meta.get('source_file', 'N/A')}, "
            f"candidate: {meta.get('candidate_name', 'N/A')}, "
            f"email: {meta.get('candidate_email', 'N/A')}) ---\n"
            f"{c['document']}\n"
        )
    resume_text = "\n".join(formatted_chunks)

    # Invoke the Screener LLM
    try:
        llm = get_llm(temperature=0.1)
        chain = SCREENER_PROMPT | llm
        response = chain.invoke({
            "job_title": job_title,
            "job_description": job_description,
            "required_skills": required_skills,
            "experience_years": experience_years,
            "resume_chunks": resume_text,
        })
        shortlisted = _parse_json_from_llm(response.content)
        # Deduplicate by name (keep highest score)
        seen = {}
        for c in shortlisted:
            name = c.get("name", "Unknown")
            if name not in seen or c.get("match_score", 0) > seen[name].get("match_score", 0):
                seen[name] = c
        shortlisted = list(seen.values())

        return {
            "shortlisted_candidates": shortlisted,
            "retrieved_chunks": chunks,
            "error": None,
        }
    except Exception as exc:
        logger.exception("Screening failed")
        return {
            "shortlisted_candidates": [],
            "retrieved_chunks": chunks,
            "error": f"Screening error: {exc}",
        }


# ──────────────────────────────────────────────────────────────────────────────
# Node 3: Schedule Interviews
# ──────────────────────────────────────────────────────────────────────────────

def schedule_interviews(state: HRState) -> dict:
    """Ask the Scheduler Agent to assign interview slots."""
    logger.info("▶ Node: schedule_interviews")
    shortlisted = state.get("shortlisted_candidates", [])
    if not shortlisted:
        return {"scheduled_candidates": [], "error": state.get("error")}

    try:
        llm = get_llm(temperature=0.3)
        chain = SCHEDULER_PROMPT | llm
        response = chain.invoke({
            "candidates_json": json.dumps(shortlisted, indent=2),
        })
        scheduled = _parse_json_from_llm(response.content)

        # Merge schedule back into shortlisted data
        slot_map = {s.get("name", ""): s.get("interview_slot", "") for s in scheduled}
        for c in shortlisted:
            c["interview_slot"] = slot_map.get(c.get("name", ""), "TBD")

        return {"scheduled_candidates": shortlisted, "error": None}
    except Exception as exc:
        logger.exception("Scheduling failed")
        # Fallback: set TBD slots
        for c in shortlisted:
            c["interview_slot"] = "TBD"
        return {"scheduled_candidates": shortlisted, "error": f"Scheduling error: {exc}"}


# ──────────────────────────────────────────────────────────────────────────────
# Node 4: Draft Emails
# ──────────────────────────────────────────────────────────────────────────────

def draft_emails(state: HRState) -> dict:
    """Ask the Communicator Agent to draft personalised emails."""
    logger.info("▶ Node: draft_emails")
    scheduled = state.get("scheduled_candidates", [])
    job_title = state.get("job_title", "")

    if not scheduled:
        return {"email_drafts": [], "error": state.get("error")}

    try:
        llm = get_llm(temperature=0.4)
        chain = COMMUNICATOR_PROMPT | llm
        response = chain.invoke({
            "job_title": job_title,
            "scheduled_json": json.dumps(scheduled, indent=2),
        })
        drafts = _parse_json_from_llm(response.content)
        return {"email_drafts": drafts, "error": None}
    except Exception as exc:
        logger.exception("Email drafting failed")
        return {"email_drafts": [], "error": f"Email drafting error: {exc}"}


# ──────────────────────────────────────────────────────────────────────────────
# Node 5: Send Emails
# ──────────────────────────────────────────────────────────────────────────────

def send_emails(state: HRState) -> dict:
    """
    Send the drafted emails via Django's send_mail.
    This node runs automatically without requiring human approval.
    """
    logger.info("▶ Node: send_emails (automatic)")
    from django.core.mail import send_mail as django_send_mail
    from django.conf import settings as django_settings

    drafts = state.get("email_drafts", [])
    sent_count = 0
    errors = []

    for draft in drafts:
        to_email = draft.get("email", "")
        subject = draft.get("subject", "Interview Invitation")
        body = draft.get("body", "")
        name = draft.get("name", "Candidate")

        if not to_email:
            logger.warning("No email for candidate %s — skipping.", name)
            errors.append(f"No email for {name}")
            continue

        try:
            django_send_mail(
                subject=subject,
                message=body,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info("✉ Email sent to %s (%s)", name, to_email)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            errors.append(f"Failed: {to_email} — {exc}")

    error_msg = "; ".join(errors) if errors else None
    return {"emails_sent": True, "error": error_msg}


# ──────────────────────────────────────────────────────────────────────────────
# Graph Construction
# ──────────────────────────────────────────────────────────────────────────────

# Shared MemorySaver for checkpoint persistence (in-memory for dev)
memory = MemorySaver()


def build_graph() -> StateGraph:
    """
    Construct and compile the HR recruitment LangGraph.

    Flow:  ingest → screen → schedule → draft_emails → send_emails → END
    """
    graph = StateGraph(HRState)

    # Add nodes
    graph.add_node("ingest_resumes", ingest_resumes)
    graph.add_node("screen_candidates", screen_candidates)
    graph.add_node("schedule_interviews", schedule_interviews)
    graph.add_node("draft_emails", draft_emails)
    graph.add_node("send_emails", send_emails)

    # Define edges (linear pipeline)
    graph.set_entry_point("ingest_resumes")
    graph.add_edge("ingest_resumes", "screen_candidates")
    graph.add_edge("screen_candidates", "schedule_interviews")
    graph.add_edge("schedule_interviews", "draft_emails")
    graph.add_edge("draft_emails", "send_emails")
    graph.add_edge("send_emails", END)

    # Compile without interrupt_before so the graph runs end-to-end
    compiled = graph.compile(
        checkpointer=memory,
    )
    return compiled


# Module-level compiled graph singleton
hr_graph = build_graph()
