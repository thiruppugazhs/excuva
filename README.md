<div align="center">

  <img src="static/img/excuva-app-icon.png" alt="Excuva Logo" width="96" height="96" style="border-radius: 24px; margin-bottom: 12px; box-shadow: 0 10px 25px -5px rgba(180, 83, 9, 0.3);" />

  # EXCUVA
  ### AI-Powered Intelligent Explanation & Communications Engine

  <p align="center">
    <strong>Turn any difficult situation into a clear, natural, and context-aware explanation.</strong>
  </p>

  <p align="center">
    <a href="https://excuva.thiruppugazhs.in"><img src="https://img.shields.io/badge/Live_Website-excuva.thiruppugazhs.in-b45309?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Live Website" /></a>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
    <img src="https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
    <img src="https://img.shields.io/badge/Neon-PostgreSQL-00E599?style=for-the-badge&logo=postgresql&logoColor=black" alt="Neon PostgreSQL" />
    <img src="https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Google Gemini" />
  </p>

  <p align="center">
    <a href="https://excuva.thiruppugazhs.in"><strong>Explore Live Web App →</strong></a> ·
    <a href="https://excuva.thiruppugazhs.in/#features">Features</a> ·
    <a href="https://excuva.thiruppugazhs.in/#privacy">Privacy Policy</a> ·
    <a href="https://excuva.thiruppugazhs.in/#terms">Terms of Service</a>
  </p>

</div>

---

## 🌟 Overview

**Excuva** is an intelligent communication assistant designed to bridge the gap between high-stress real-world disruptions and professional, believable communication. Whether facing a missed deadline, an emergency absence, transport delays, or rescheduling needs, Excuva calibrates the tone, length, delivery channel, and recipient dynamics to craft the ideal response.

### 🌐 Live Platform
Access the fully deployed production application at:  
👉 **[https://excuva.thiruppugazhs.in](https://excuva.thiruppugazhs.in)**

---

## ✨ Key Highlights & Capabilities

### 🎯 6-Step Contextual Wizard
- **Situation Description**: Natural language input with character counters and smart scenario templates.
- **Recipient Calibration**: Customizes greetings, salutations, and phrasing for *Professors, Teachers, Managers, Employers, Clients, Friends, Parents, Colleagues*, or *Custom roles*.
- **Category Inference**: Automatically infers situation category (*Missed deadline, Late arrival, Unable to attend, Need extension, Cancel appointment, Forgot something, Didn't reply*).
- **Tone Matrix**: Select from *Professional, Formal, Casual, Apologetic, Direct,* or *Friendly*.
- **Length Control**: Adjust output volume from *Very Short (1 sentence)* to *Detailed (2-3 structured paragraphs)*.
- **Channel-Specific Formatting**: Formats specifically for *Email (with auto-generated Subject lines)*, *WhatsApp/SMS (concise mobile chat)*, *In Person (spoken dialogue scripts)*, *College Portals*, and *Workplace Chat (Slack/Teams)*.

### 🧠 Dual-Engine Architecture
- **Google Gemini Flash**: High-speed, natural language generation with contextual prompt engineering.
- **Deterministic Heuristic Engine**: Built-in instant offline/fallback generation engine that guarantees 100% uptime and sub-second responses even during external network disruptions.

### 📊 Believability & Risk Analysis
- Real-time **Believability Meter** (0–100%) and **Risk Assessment Badge** (*Low, Moderate, High*).
- **Actionable Tactical Tips**: Contextual advice on delivery timing, follow-up etiquette, and verification readiness.

### ✏️ Interactive Rewriting & Live Editing
- **1-Click Quick Transformations**: *Make Shorter, More Formal, More Casual, Friendlier, More Natural,* or *More Apologetic*.
- **Custom AI Instruction**: Change anything via freeform natural language prompts.
- **Version History & Tab Switcher**: Seamlessly branch, compare, and switch between multiple draft versions.
- **Inline Editor**: Modify and polish the drafted text directly before copying or saving.

### 📜 Formal Proof & Supporting Document Generator
- Generates official, multi-paragraph written statements:
  - 📋 **Official Request for Deadline Extension**
  - 📝 **Formal Written Explanation Letter**
  - 🛡️ **Personal Declaration of Unavoidable Circumstances**
  - 🏖️ **Formal Application for Emergency Leave**
  - ⏱️ **Official Notification of Schedule Disruption & Delay**
- Formatted with unique **Reference Numbers**, chronological breakdowns, mitigation clauses, signature lines, and **Print / PDF-ready layout**.
- Features an **Instant Undo Button** for easy generation reversal.

### 🔐 Authentication & Security Suite
- **Orbital 6-Digit Email OTP**: Secure registration, email verification, and password reset flows with real-time countdown timer and re-send capabilities.
- **Google OAuth 2.0**: Single-click Google Sign-In with backend token exchange.
- **Encrypted Sessions**: Timing-safe password hashing (PBKDF2-SHA256) and cryptographically secure tokenized sessions.
- **Privacy Controls**: Permanent 1-click account deletion and data scrubbing.

---

## 📱 Supported Delivery Channels

| Channel | Output Structure | Best For |
| :--- | :--- | :--- |
| **Email** | Includes professional `Subject:` header, formal salutation, structured body, and sign-off. | Managers, Professors, Clients, HR |
| **WhatsApp / SMS** | Crisp, conversational mobile formatting without email headers. | Friends, Colleagues, Immediate Team |
| **In Person** | Natural spoken dialogue script phrased for face-to-face conversations. | Meetings, Direct Supervisors, Teachers |
| **College Portal** | Formal academic etiquette referencing coursework and submission considerations. | Universities, Academic Portals |
| **Work Chat** | Slack/Teams style message with clear action items and collaboration context. | Remote teams, Standups, Slack |

---

## 🛠️ Architecture & Tech Stack

```
                                  ┌─────────────────────────────┐
                                  │      EXCUVA Web Client      │
                                  │ (HTML5 / Tailwind / Vanilla)│
                                  └──────────────┬──────────────┘
                                                 │ HTTPS / REST
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │     Flask API Backend       │
                                  │    (WSGI / Python 3.10+)    │
                                  └──────┬───────────────┬──────┘
                                         │               │
                 ┌───────────────────────┴──────┐ ┌──────┴───────────────────────┐
                 ▼                              ▼ ▼                               ▼
   ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
   │     Google Gemini AI      │ │   Neon Serverless Postgres│ │     SMTP Mail Service     │
   │  (Generative AI Engine)   │ │ (Persistent Data Storage) │ │  (Orbital OTP Dispatch)   │
   └───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

### 💻 Technologies
- **Frontend**: Responsive Single Page Application (SPA), Tailwind CSS, Modern Typography, Dark/Light Warm Theme Engine.
- **Backend**: Python 3, Flask RESTful Architecture, Google GenAI SDK.
- **Database**: Neon Serverless PostgreSQL with auto-migrating SQLite fallback.
- **Security**: Google OAuth 2.0, Werkzeug Security, SMTP OTP Verification.

---

## 📂 Project Structure

```
AI-Powered-Intelligent-Excuse-Generator/
├── app.py                      # Flask Application Server & API Routes
├── ai_engine.py                # AI Integration & Contextual Fallback Engine
├── database.py                 # SQLite Data Layer
├── neon_db.py                  # Neon PostgreSQL Data Layer & Migrations
├── static/                     # Static Web Assets
│   ├── index.html              # Main Single Page Application Entry
│   ├── css/
│   │   └── styles.css          # Custom Styles & Warm Theme Palettes
│   ├── js/
│   │   ├── app.js              # Application Core & View Router
│   │   ├── auth.js             # OTP & OAuth Authentication Manager
│   │   ├── generator.js        # 6-Step Explanation Wizard & Live Editor
│   │   ├── documents.js        # Proof & Supporting Document Generator
│   │   ├── history.js          # Archive, Search & Starred Collection
│   │   └── profile_settings.js # User Preferences & Theme Controller
│   └── img/
│       └── excuva-app-icon.png # Application Icon & Branding
├── requirements.txt            # Python Dependencies
├── vercel.json                 # Cloud Deployment Configuration
└── README.md                   # Project Documentation
```

---

## ⚙️ Environment Variables Reference

For production deployments, the following configuration parameters are supported:

| Variable | Description | Required |
| :--- | :--- | :---: |
| `NEON_DATABASE_URL` | Neon Serverless PostgreSQL connection string | Yes (for Postgres) |
| `GOOGLE_API_KEY` | Google Gemini API key for AI generation | Optional (has built-in fallback) |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Web Client ID | Optional (for Google Sign-In) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | Optional (for Google Sign-In) |
| `SMTP_SERVER` | SMTP Host (e.g., `smtp.gmail.com`) | Optional (for live email OTPs) |
| `SMTP_PORT` | SMTP Port (`587` or `465`) | Optional |
| `SMTP_EMAIL` | Sender Email Address | Optional |
| `SMTP_PASSWORD` | App-Specific Password for SMTP | Optional |

---

## 📄 Privacy & Terms

- **Privacy Policy**: [https://excuva.thiruppugazhs.in/#privacy](https://excuva.thiruppugazhs.in/#privacy)
- **Terms of Service**: [https://excuva.thiruppugazhs.in/#terms](https://excuva.thiruppugazhs.in/#terms)

---

<div align="center">
  <p><strong>Excuva</strong> — Crafted for intelligent, believable, and respectful communication.</p>
  <p>© 2026 Excuva. All rights reserved.</p>
</div>
