# AutoProspect Multi-Agent

AutoProspect Multi-Agent is an automated prospecting and outreach tool that leverages Groq (Llama 3) and Serper API to streamline B2B outreach. It autonomously identifies potential target companies, finds relevant decision-makers, uncovers genuine research insights from company websites and Reddit, and generates tailored outreach emails.

## Features

- **Automated Research:** Finds and evaluates target companies based on user-defined criteria.
- **Contact Identification:** Automatically identifies high-value decision-makers and generates inferred email addresses.
- **Intelligent Personalization:** Gathers insights from company websites and Reddit to write highly relevant outreach emails.
- **Multi-Agent Workflow:** Orchestrates specialized agents for company finding, contact discovery, research, and email composition.

## Agent Architecture and Workflow

AutoProspect Multi-Agent utilizes a sequential, multi-agent pipeline where each agent relies on the output of its predecessor. This modular design allows for specialized processing at each stage of the lead generation and outreach process.

### Workflow

1. **Company Finder Agent:** Initiates the pipeline by searching for target companies based on user criteria.
2. **Contact Finder Agent:** Processes the list of companies to identify key decision-makers and their contact details.
3. **Research Agent:** Conducts deep research on the identified companies to gather specific insights for personalization.
4. **Email Writer Agent:** Synthesizes the contact information and research insights to craft tailored outreach emails.

### Agent Summary

| Agent Name | Responsibility | Key Task |
| :--- | :--- | :--- |
| **Company Finder** | Lead Generation | Search for companies matching targeting criteria. |
| **Contact Finder** | Prospecting | Identify decision-makers and infer email patterns. |
| **Research Agent** | Personalization | Gather insights from websites and Reddit. |
| **Email Writer** | Outreach | Generate personalized email content. |

## Prerequisites

- Python 3.10+
- Groq API Key (https://console.groq.com/)
- Serper API Key (https://serper.dev/)

- **Framework:** Streamlit, Agno (formerly Phidata)
- **LLM Provider:** Groq (Llama 3.1 8b-instant)
- **Search API:** Serper.dev
## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run ai_email_gtm_outreach_agent.py
   ```

2. Open the provided local URL in your browser.

3. Enter your Groq API Key and Serper API Key in the sidebar.

4. Fill in the required fields:
   - Target companies (industry, size, region, etc.)
   - Your product/service offering
   - Your name and company
   - Number of companies to prospect

5. Click "Start Outreach" to begin the automated pipeline.

## Application Showcase

The following screenshots demonstrate the AutoProspect Multi-Agent in action, from input configuration to the generation of highly personalized B2B outreach emails:

### Input Configuration
![Input Configuration](assets/screenshots/Screenshot%20(10487).png)

### Generated Results
The application successfully identifies target companies, discovers key contacts, performs deep research on their current initiatives, and drafts highly tailored emails:

![Top Target Companies](assets/screenshots/Screenshot%20(10482).png)
![Contacts Found](assets/screenshots/Screenshot%20(10489).png)
![Research Insights](assets/screenshots/Screenshot%20(10491).png)
![Outreach Emails](assets/screenshots/Screenshot%20(10493).png)

