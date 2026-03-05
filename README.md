# 🔍 AI/SEO Audit Tool

An automated SEO and AI-readiness audit tool built with Streamlit and powered by OpenAI GPT-4o.

## Features

Audits your website across 10 weighted criteria:

| Criterion | Priority | Weight |
|---|---|---|
| 🏗️ Structured Data | High | 3x |
| ♿ ARIA & Accessibility | High | 3x |
| 📄 Content Structure | High | 3x |
| 🏷️ Meta Tags & Title | High | 3x |
| 🤖 LLMs.txt | Medium | 2x |
| ⚡ Page Speed Signals | Medium | 2x |
| 🔗 Internal Linking | Medium | 2x |
| 📱 Mobile Readiness | Medium | 2x |
| 🔒 Security & HTTPS | Low | 1x |
| 📣 Social Sharing | Low | 1x |

Scores are weighted by priority, giving you a realistic overall score that reflects what matters most for SEO and AI discoverability.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/seo-audit-tool.git
cd seo-audit-tool
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

1. Enter your OpenAI API key in the sidebar (GPT-4o access required).
2. Select which criteria to include in the audit.
3. Paste your website URL and click **Run Audit**.
4. Review scores, findings, and recommendations per criterion.
5. Download the HTML report for sharing.

---

## Deploying to Streamlit Community Cloud

1. Push the repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set `app.py` as the entry point.
4. Add your `OPENAI_API_KEY` as a secret in the Streamlit dashboard (optional -- users can also enter it in the sidebar at runtime).

---

## Project Structure

```
seo-audit-tool/
├── app.py              # Main Streamlit UI
├── auditor.py          # Page fetching + OpenAI analysis
├── scoring.py          # Criteria definitions + score calculation
├── report.py           # HTML report generator
├── requirements.txt
├── .streamlit/
│   └── config.toml     # Streamlit theme config
└── README.md
```

---

## Notes

- The tool fetches your page HTML and sends it to OpenAI for analysis. No data is stored.
- LLMs.txt is checked automatically by fetching `/llms.txt` from the root domain.
- HTML is truncated at ~80,000 characters to stay within GPT-4o's context window efficiently.
- Each criterion uses a tailored prompt to focus the model's attention on the right signals.

---

## Extending the Tool

To add a new criterion:

1. Add an entry to `AUDIT_CRITERIA` in `scoring.py` with a label, icon, priority, and weight.
2. Add a matching prompt to `CRITERION_PROMPTS` in `auditor.py`.

That's it -- the UI and scoring will pick it up automatically.
