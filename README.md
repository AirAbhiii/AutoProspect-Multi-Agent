# AutoProspect Multi-Agent

AutoProspect Multi-Agent is an automated prospecting and outreach tool that leverages Groq (Llama 3) and Serper API to streamline B2B outreach. It autonomously identifies potential target companies, finds relevant decision-makers, uncovers genuine research insights from company websites and Reddit, and generates tailored outreach emails.

## Features

- **Automated Research:** Finds and evaluates target companies based on user-defined criteria.
- **Contact Identification:** Automatically identifies high-value decision-makers and generates inferred email addresses.
- **Intelligent Personalization:** Gathers insights from company websites and Reddit to write highly relevant outreach emails.
- **Multi-Agent Workflow:** Orchestrates specialized agents for company finding, contact discovery, research, and email composition.

## Prerequisites

- Python 3.10+
- Groq API Key (https://console.groq.com/)
- Serper API Key (https://serper.dev/)

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

## Configuration

This application requires the following environment variables (or can be provided via the sidebar):
- `GROQ_API_KEY`
- `SERPER_API_KEY`

## Built With

- **Framework:** Streamlit, Agno (formerly Phidata)
- **LLM Provider:** Groq (Llama 3.1 8b-instant)
- **Search API:** Serper.dev
