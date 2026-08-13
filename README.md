# ✈️ PreFlight AI

> **Review AI systems before they reach production.**

PreFlight AI is a production-focused AI engineering review platform that analyzes AI system architectures before they are deployed.

Instead of asking a generic LLM for feedback, PreFlight AI simulates a **Design Review Board**, where specialized reviewers evaluate an AI system across engineering dimensions such as:

- 📈 Scalability
- 🔒 Security
- 👀 Observability
- ⚙️ Reliability
- 💰 Cost

The goal is simple:

> Catch architectural issues **before** they become production incidents.

---

# 📸 Preview

Homepage:
<img width="512" height="320" alt="homepage" src="https://github.com/user-attachments/assets/3fb006d2-58aa-495e-adff-fbaa88382a67" />


---

# 🚀 Why I Built This

While building production AI systems, I noticed something interesting.

Most architecture reviews happen:

- after development
- during code review
- or even worse... after deployment

I wanted to explore a different idea.

**What if an AI system could perform a structured architecture review before a single line of production code is written?**

PreFlight AI is my attempt at answering that question.

---

# ✨ Current Features (v1.0)

✅ Interactive Design Review Board

✅ Production-style engineering report

✅ Rule-based engineering reviewers

✅ Example AI architectures

✅ Executive dashboard

✅ Engineering recommendations

✅ Professional review workflow

---

# 🎬 How It Works

1. Choose an example architecture (or fill out your own)

2. Convene the Design Review Board

3. Specialized reviewers evaluate the architecture

4. Reviewers vote

5. Receive an executive engineering report

---

# 📷 Screenshots

## Example Architectures

<img width="512" height="205" alt="example-architectures" src="https://github.com/user-attachments/assets/a2aea40a-757b-4234-a705-ac42b4b7dc4a" />


---

## Design Review Board

<img width="512" height="212" alt="ai-design-review-board" src="https://github.com/user-attachments/assets/3a33f2c5-62a4-4040-80aa-bc10c9ffda62" />


---

## Executive Report

<img width="512" height="321" alt="review-board-summary" src="https://github.com/user-attachments/assets/36791897-5da6-4cf6-92f7-1593e5a9b0b9" />


---

## Detailed Engineering Review

<img width="512" height="375" alt="detail-report-1" src="https://github.com/user-attachments/assets/e4502ebf-84fe-4f3f-a4c8-2a3b7ac81693" />
<img width="512" height="240" alt="detail-report-2" src="https://github.com/user-attachments/assets/92105266-51ad-4fef-9b7f-7d9a588a3302" />
<img width="512" height="236" alt="detail-report-3" src="https://github.com/user-attachments/assets/6a7bc1ec-3e7b-4c90-b22e-99c7cc093a95" />
<img width="512" height="241" alt="detail-report-4" src="https://github.com/user-attachments/assets/55061cd9-2a9b-4be5-a91d-a646e3700914" />
<img width="512" height="248" alt="detail-report-5" src="https://github.com/user-attachments/assets/496e67d5-08a8-4b0b-bd5b-b8b72ab0ed35" />


---

# 🏗 Architecture

```
                    User

                      │

                      ▼

          Next.js Frontend

                      │

                      ▼

            FastAPI Backend

                      │

                      ▼

        Design Review Service

                      │

     ┌────────────────────────────────┐
     │                                │
     ▼                                ▼

Scalability Reviewer        Security Reviewer

Observability Reviewer      Reliability Reviewer

Cost Reviewer

                      │

                      ▼

            Review Board Decision

                      │

                      ▼

         Engineering Report
```

---

# ⚙️ Tech Stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- FastAPI
- Python 3.12
- Pydantic

## Architecture

- Clean Architecture
- Service Layer Pattern
- Strategy Pattern (Reviewers)

---

# 🤔 Why Not Just Use ChatGPT?

That's a fair question.

ChatGPT can certainly review an architecture if you paste it into a prompt.

PreFlight AI focuses on something different.

| ChatGPT | PreFlight AI |
|----------|--------------|
| Generic conversation | Structured engineering workflow |
| One response | Multiple specialized reviewers |
| Free-form output | Executive engineering report |
| No review process | Simulated Design Review Board |
| Prompt dependent | Consistent evaluation workflow |

Future versions will also include:

- LLM reviewers
- Architecture knowledge base
- GitHub repository review
- Prompt review
- RAG review

---

# 🗺 Roadmap

## ✅ Version 1.0

- [x] Rule-based reviewers
- [x] Review Board
- [x] Executive report
- [x] Example architectures
- [x] Responsive UI

---

## 🚧 Version 2.0

- [ ] LLM-powered reviewers
- [ ] Multi-agent review workflow
- [ ] Confidence scoring
- [ ] Architecture knowledge base

---

## 🚀 Version 3.0

- [ ] Mermaid diagram upload
- [ ] Repository analysis
- [ ] Prompt review
- [ ] RAG review
- [ ] Agent workflow review

---

# 🛠 Running Locally

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 📂 Repository Structure

```
backend/
    api/
    services/
    reviewers/
    schemas/
    prompts/

frontend/
    app/
    components/
    lib/
    services/
    types/
```

---

# 🎯 Vision

PreFlight AI is the first module of a broader AI Engineering platform.

Future modules will review:

- AI Architectures
- Prompt Engineering
- RAG Systems
- AI Agents
- GitHub Repositories
- Production Readiness

The long-term vision is to build an engineering copilot that helps teams design better AI systems before they reach production.

---

# 👨‍💻 Author

**Ishan Bansal**

AI / ML Engineer

Building production AI systems with LLMs, RAG, NLP, and AI Agents.

If this project interests you, feel free to connect or contribute.

---

# ⭐ Support

If you found this project interesting, consider giving it a ⭐.

It helps others discover the project and motivates future development.
