import json
import os
import sys
from typing import Any, Dict, List, Optional

import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.db.sqlite import SqliteDb
from agno.models.groq import Groq


def require_env(var_name: str) -> None:
    if not os.getenv(var_name):
        print(f"Error: {var_name} not set. export {var_name}=...")
        sys.exit(1)


def create_company_finder_agent() -> Agent:
    return Agent(
        model=Groq(id="llama-3.1-8b-instant"),
        tools=[],
        enable_user_memories=True,
        add_history_to_context=False,
        num_history_runs=0,
        debug_mode=True,
        instructions=[
            "You are an AI agent. You have exactly ONE tool available: SerperTools.",
            "FORBIDDEN: Do NOT use 'brave_search', 'scrape_webpage', or 'google_search'. These tools do not exist in this environment.",
            "If you need information from the web, you MUST use SerperTools.",
            "You are CompanyFinderAgent. Find the BEST possible fits for the user's criteria. Do not be overly restrictive; provide likely fits if exact ones are missing.",
            "MANDATE: You MUST return a list of companies. NEVER return an empty list.",
            "Return ONLY valid JSON with key 'companies' as a list; each item must have: name, website, why_fit (1-2 lines).",
        ],
    )


def create_contact_finder_agent() -> Agent:
    serper_tools = SerperTools()
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    return Agent(
        model=Groq(id="llama-3.1-8b-instant"),
        tools=[],
        enable_user_memories=True,
        add_history_to_context=False,
        num_history_runs=0,
        debug_mode=True,
        instructions=[
            "You are ContactFinderAgent. Your goal is to identify REAL high-value decision makers.",
            "MANDATE: Return ONLY a valid JSON object. Do NOT include any preambles, thoughts, or notes.",
            "CRITICAL: Do NOT use comments (e.g., // or #) inside the JSON. Standard JSON does not support comments.",
            "CRITICAL: NEVER use placeholder names like 'John Doe' or 'Jane Smith'. Use 'Unknown' if not found.",
            "STEP 1: Search for real names and titles using SerperTools (e.g., 'site:linkedin.com/in/ [Company] CEO').",
            "STEP 2: If a real name is found, then search for their email or the company's email pattern.",
            "If a real name is found but no email is found, you may infer the email and mark inferred=true.",
            "Prioritize roles: Founder, CEO, VP of Growth, Head of Sales, or Product Marketing.",
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, contacts: [{full_name, title, email, inferred}]",
        ],
    )


def get_email_style_instruction(style_key: str) -> str:
    styles = {
        "Professional": "Style: Professional. Clear, respectful, and businesslike. Short paragraphs; no slang.",
        "Casual": "Style: Casual. Friendly, approachable, first-name basis. No slang or emojis; keep it human.",
        "Cold": "Style: Cold email. Strong hook in opening 2 lines, tight value proposition, minimal fluff, strong CTA.",
        "Consultative": "Style: Consultative. Insight-led, frames observed problems and tailored solution hypotheses; soft CTA.",
    }
    return styles.get(style_key, styles["Professional"])


def create_email_writer_agent(style_key: str = "Professional") -> Agent:
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    style_instruction = get_email_style_instruction(style_key)
    return Agent(
        model=Groq(id="llama-3.1-8b-instant"),
        tools=[],
        enable_user_memories=True,
        add_history_to_context=False,
        num_history_runs=0,
        session_id="gtm_outreach_email_writer",
        debug_mode=False,
        instructions=[
            "You are EmailWriterAgent. Write concise, personalized B2B outreach emails.",
            style_instruction,
            "MANDATE: Return ONLY a valid JSON object. Do NOT include any conversational filler, preambles, or notes.",
            "CRITICAL: The 'body' field must be a single string. NEVER use string concatenation (e.g., do NOT use '+'). Use '\\n' for newlines.",
            "Return ONLY valid JSON with key 'emails' as a list of items: {company, contact, subject, body}.",
            "Length: 120-160 words. Include 1-2 lines of strong personalization referencing research insights (company website and Reddit findings).",
            "CTA: suggest a short intro call; include sender company name and calendar link if provided.",
        ],
    )


def create_research_agent() -> Agent:
    """Agent to gather interesting insights from company websites and Reddit."""
    serper_tools = SerperTools()
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    return Agent(
        model=Groq(id="llama-3.1-8b-instant"),
        tools=[],
        enable_user_memories=True,
        add_history_to_context=False,
        num_history_runs=0,
        session_id="gtm_outreach_researcher",
        debug_mode=True,
        instructions=[
            "You are ResearchAgent. For each company, you MUST find 2-4 valuable insights.",
            "Search targets: 1) Official website (About, Blog, Product), 2) Recent News/Press Releases, 3) Reddit or industry forums.",
            "Avoid generic statements like 'They provide great service'. Look for: recent funding, new product launches, specific target markets, or unique value props.",
            "MANDATE: Do not return an empty list. If no specific news is found, analyze their website and summarize their primary business goal.",
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, insights: [strings].",
        ],
    )


def extract_json_or_raise(text: str) -> Dict[str, Any]:
    """Extract JSON from a model response. Handles common small-model errors and trailing text."""
    try:
        # 1. Try standard JSON loading
        return json.loads(text)
    except Exception:
        try:
            # 2. Try to isolate the FIRST JSON block
            start = text.find("{")
            if start == -1:
                raise ValueError("No opening brace found")
                
            # We need to find the matching closing brace for the FIRST block
            bracket_count = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    bracket_count += 1
                elif text[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        candidate = text[start : i + 1]
                        # Fix common small-model error: using single quotes instead of double quotes
                        if "'" in candidate and '"' not in candidate:
                            candidate = candidate.replace("'", '"')
                        return json.loads(candidate)
            
            raise ValueError("No matching closing brace found")
        except Exception as e:
            raise ValueError(f"Failed to parse JSON. Response was: {text}") from e


import requests

def run_company_finder(agent: Agent, target_desc: str, offering_desc: str, max_companies: int) -> List[Dict[str, str]]:
    # Manual Search using Serper API
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": f"B2B companies matching: {target_desc} for {offering_desc}"})
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        search_results = response.text
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt = (
        f"DATA TO ANALYZE:\n{search_results}\n\n"
        f"TASK: Extract {max_companies} companies that fit these criteria: {target_desc}\n"
        f"Product Offering: {offering_desc}\n\n"
        "STRICT RULES:\n"
        "1. Return ONLY a valid JSON object. No conversational text. No preambles. No notes.\n"
        "2. NEVER write Python code, scripts, or functions. Do NOT use ```python blocks.\n"
        "3. Response must start with { and end with }.\n"
        "4. If exact matches are missing, provide the closest possible B2B fits. NEVER return an empty list.\n\n"
        "JSON FORMAT: {'companies': [{'name': '...', 'website': '...', 'why_fit': '...'}]}"
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    companies = data.get("companies", [])
    return companies[: max(1, min(max_companies, 10))]


def run_contact_finder(agent: Agent, companies: List[Dict[str, str]], target_desc: str, offering_desc: str) -> List[Dict[str, Any]]:
    prompt = (
        "For each company below, find 2-3 relevant decision makers and emails (if available). Ensure at least 2 per company when possible, and cap at 3.\n"
        "If not available, infer likely email and mark inferred=true.\n"
        f"Targeting: {target_desc}\nOffering: {offering_desc}\n"
        f"Companies JSON: {json.dumps(companies, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, contacts: [{full_name, title, email, inferred}]}]}"
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])


def run_research(agent: Agent, companies: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    prompt = (
        "For each company, gather 2-4 interesting insights from their website and Reddit that would help personalize outreach.\n"
        f"Companies JSON: {json.dumps(companies, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, insights: [string, ...]}]}"
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])


def run_email_writer(agent: Agent, contacts_data: List[Dict[str, Any]], research_data: List[Dict[str, Any]], offering_desc: str, sender_name: str, sender_company: str, calendar_link: Optional[str]) -> List[Dict[str, str]]:
    prompt = (
        "Write personalized outreach emails for the following contacts.\n"
        f"Sender: {sender_name} at {sender_company}.\n"
        f"Offering: {offering_desc}.\n"
        f"Calendar link: {calendar_link or 'N/A'}.\n"
        f"Contacts JSON: {json.dumps(contacts_data, ensure_ascii=False)}\n"
        f"Research JSON: {json.dumps(research_data, ensure_ascii=False)}\n"
        "Return JSON with key 'emails' as a list of {company, contact, subject, body}."
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("emails", [])


def run_pipeline(target_desc: str, offering_desc: str, sender_name: str, sender_company: str, calendar_link: Optional[str], num_companies: int):
    company_agent = create_company_finder_agent()
    contact_agent = create_contact_finder_agent()
    research_agent = create_research_agent()

    companies = run_company_finder(company_agent, target_desc, offering_desc, max_companies=num_companies)
    contacts_data = run_contact_finder(contact_agent, companies, target_desc, offering_desc) if companies else []
    research_data = run_research(research_agent, companies) if companies else []
    return {
        "companies": companies,
        "contacts": contacts_data,
        "research": research_data,
        "emails": [],
    }


def main() -> None:
    st.set_page_config(page_title="AutoProspect Multi-Agent", layout="wide")

    # Sidebar: API keys
    st.sidebar.header("API Configuration")
    groq_key = st.sidebar.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    serper_key = st.sidebar.text_input("Serper API Key", type="password", value=os.getenv("SERPER_API_KEY", ""))
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    if serper_key:
        os.environ["SERPER_API_KEY"] = serper_key

    if not groq_key or not serper_key:
        st.sidebar.warning("Enter both API keys to enable the app")

    # Inputs
    st.title("AutoProspect Multi-Agent")
    st.info(
        "Professionals often struggle with the slow pace of manual research and outreach personalization. "
        "AutoProspect automates this using Groq (Llama 3) and Serper, powered by a multi-agent workflow. "
        "It autonomously identifies potential partners, finds relevant contacts, uncovers genuine research insights from company websites and Reddit, "
        "and generates tailored outreach emails in your chosen style."
    )
    col1, col2 = st.columns(2)
    with col1:
        target_desc = st.text_area("Target companies (industry, size, region, tech, etc.)", height=100)
        offering_desc = st.text_area("Your product/service offering (1-3 sentences)", height=100)
    with col2:
        sender_name = st.text_input("Your name", value="Sales Team")
        sender_company = st.text_input("Your company", value="Our Company")
        calendar_link = st.text_input("Calendar link (optional)", value="")
        num_companies = st.number_input("Number of companies", min_value=1, max_value=10, value=5)
        email_style = st.selectbox(
            "Email style",
            options=["Professional", "Casual", "Cold", "Consultative"],
            index=0,
            help="Choose the tone/format for the generated emails",
        )

    if st.button("Start Outreach", type="primary"):
        # Validate
        if not groq_key or not serper_key:
            st.error("Please provide API keys in the sidebar")
        elif not target_desc or not offering_desc:
            st.error("Please fill in target companies and offering")
        else:
            # Stage-by-stage progress UI
            progress = st.progress(0)
            stage_msg = st.empty()
            details = st.empty()
            try:
                # Prepare agents
                company_agent = create_company_finder_agent()
                contact_agent = create_contact_finder_agent()
                research_agent = create_research_agent()
                email_agent = create_email_writer_agent(email_style)

                # 1. Companies
                stage_msg.info("1/4 Finding companies...")
                companies = run_company_finder(
                    company_agent,
                    target_desc.strip(),
                    offering_desc.strip(),
                    max_companies=int(num_companies),
                )
                progress.progress(25)
                details.write(f"Found {len(companies)} companies")

                # 2. Contacts
                stage_msg.info("2/4 Finding contacts (2–3 per company)...")
                contacts_data = run_contact_finder(
                    contact_agent,
                    companies,
                    target_desc.strip(),
                    offering_desc.strip(),
                ) if companies else []
                progress.progress(50)
                details.write(f"Collected contacts for {len(contacts_data)} companies")

                # 3. Research
                stage_msg.info("3/4 Researching insights (website + Reddit)...")
                research_data = run_research(research_agent, companies) if companies else []
                progress.progress(75)
                details.write(f"Compiled research for {len(research_data)} companies")

                # 4. Emails
                stage_msg.info("4/4 Writing personalized emails...")
                emails = run_email_writer(
                    email_agent,
                    contacts_data,
                    research_data,
                    offering_desc.strip(),
                    sender_name.strip() or "Sales Team",
                    sender_company.strip() or "Our Company",
                    calendar_link.strip() or None,
                ) if contacts_data else []
                progress.progress(100)
                details.write(f"Generated {len(emails)} emails")

                st.session_state["gtm_results"] = {
                    "companies": companies,
                    "contacts": contacts_data,
                    "research": research_data,
                    "emails": emails,
                }
                stage_msg.success("Completed")
            except Exception as e:
                stage_msg.error("Pipeline failed")
                st.error(f"{e}")

    # Show results if present
    results = st.session_state.get("gtm_results")
    if results:
        companies = results.get("companies", [])
        contacts = results.get("contacts", [])
        research = results.get("research", [])
        emails = results.get("emails", [])

        st.subheader("Top target companies")
        if companies:
            for idx, c in enumerate(companies, 1):
                st.markdown(f"**{idx}. {c.get('name','')}**  ")
                st.write(c.get("website", ""))
                st.write(c.get("why_fit", ""))
        else:
            st.info("No companies found")
        st.divider()

        st.subheader("Contacts found")
        if contacts:
            for c in contacts:
                st.markdown(f"**{c.get('name','')}**")
                for p in c.get("contacts", [])[:3]:
                    inferred = " (inferred)" if p.get("inferred") else ""
                    st.write(f"- {p.get('full_name','')} | {p.get('title','')} | {p.get('email','')}{inferred}")
        else:
            st.info("No contacts found")
        st.divider()

        st.subheader("Research insights")
        if research:
            for r in research:
                st.markdown(f"**{r.get('name','')}**")
                for insight in r.get("insights", [])[:4]:
                    st.write(f"- {insight}")
        else:
            st.info("No research insights")
        st.divider()

        st.subheader("Suggested Outreach Emails")
        if emails:
            for i, e in enumerate(emails, 1):
                with st.expander(f"{i}. {e.get('company','')} → {e.get('contact','')}"):
                    st.write(f"Subject: {e.get('subject','')}")
                    st.text(e.get("body", ""))
        else:
            st.info("No emails generated")


if __name__ == "__main__":
    main()
