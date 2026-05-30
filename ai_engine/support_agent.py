import logging
from django.db.models import Q
from langchain_core.prompts import ChatPromptTemplate
from ai_engine.agents import get_llm
from core.models import CompanyPolicy, FAQ

logger = logging.getLogger(__name__)

SUPPORT_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert, helpful HR Support Agent for the company.\n"
        "Your job is to answer the employee's questions accurately based ONLY on the provided context.\n\n"
        "Employee Profile Data:\n"
        "Name: {employee_name}\n"
        "Department: {department}\n"
        "Salary: ${salary}\n"
        "Leave Balance: {leave_balance} days\n"
        "Attendance Score: {attendance_score}/100\n\n"
        "Company Policy & FAQ Context:\n"
        "{context_data}\n\n"
        "RULES:\n"
        "1. Be polite, professional, and clear.\n"
        "2. If the user asks about their personal info (e.g., salary, leaves), use the Employee Profile Data.\n"
        "3. If they ask about policies, use the Company Policy & FAQ Context.\n"
        "4. DO NOT hallucinate. If the answer is not in the context, say 'I do not have that information at this time.'\n"
    ),
    ("human", "{user_message}"),
])

def generate_support_response(message: str, employee_profile) -> str:
    """
    RAG + DB lookup based Support Agent.
    """
    try:
        # 1. Very basic keyword extraction / search
        # Split message into words > 3 chars
        keywords = [w for w in message.lower().split() if len(w) > 3]
        
        # 2. Search Policies and FAQs
        policies = CompanyPolicy.objects.all()
        faqs = FAQ.objects.all()
        
        if keywords:
            # Build Q objects for basic text search
            policy_q = Q()
            faq_q = Q()
            for kw in keywords:
                policy_q |= Q(title__icontains=kw) | Q(content__icontains=kw)
                faq_q |= Q(question__icontains=kw) | Q(answer__icontains=kw)
                
            policies = policies.filter(policy_q).distinct()
            faqs = faqs.filter(faq_q).distinct()

        # 3. Format Context
        context_parts = []
        for p in policies:
            context_parts.append(f"POLICY: {p.title}\n{p.content}")
        for f in faqs:
            context_parts.append(f"FAQ: Q: {f.question}\nA: {f.answer}")
            
        context_data = "\n\n".join(context_parts)
        if not context_data:
            context_data = "No specific policy or FAQ matches found."

        # 4. Invoke LLM
        llm = get_llm(temperature=0.3)
        chain = SUPPORT_AGENT_PROMPT | llm
        
        response = chain.invoke({
            "employee_name": employee_profile.user.username,
            "department": employee_profile.department,
            "salary": employee_profile.salary or 0.0,
            "leave_balance": employee_profile.leave_balance,
            "attendance_score": employee_profile.attendance_score,
            "context_data": context_data,
            "user_message": message
        })
        
        return response.content
        
    except Exception as e:
        logger.exception("Error in support agent")
        return f"I'm sorry, I encountered an internal error while processing your request: {e}"
