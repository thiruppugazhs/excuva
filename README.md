# EXCUVA — AI-Powered Intelligent Excuse Generator

Turn any difficult situation into a clear, natural, and context-aware explanation.

## 🚀 Application Structure

### Public Website
- **Landing Page**: Modern hero section with quick CTAs and capability showcase.
- **How It Works**: 3-step intuitive guide.
- **Features**: Breakdown of tone control, recipient awareness, and supporting documents.
- **Authentication**:
  - **Create Account**: Form validation (name, valid email, duplicate check, password strength, match, terms agreement).
  - **Google OAuth**: Backend session creation and one-tap / account picker integration.
  - **Login**: Timing-safe generic error responses (`Incorrect email or password`).
  - **Forgot Password & Reset**: Secure token dispatch with interactive test link and password update flow.
- **Legal**: Privacy Policy and Terms of Service.

### Authenticated User Application
- **Dashboard**: Real-time metrics (Total Generated, Supporting Proofs, Favorites, Believability Avg) and recent history.
- **Generate Excuse**:
  - Scenario suggestions and custom inputs.
  - **Tone Control**: Professional, Casual, Friendly, Apologetic, Funny, Formal, Short & Direct.
  - **Recipient Awareness**: Manager, Employer, Professor, Teacher, Client, Friend, Parent, Colleague, Other.
  - **Urgency Levels**: Low, Medium, High, Critical.
  - Primary drafted explanation with Believability meter, Risk level badge, and actionable follow-up checklist.
  - Alternative variations (Direct/Concise & Context-Rich).
- **AI Rewriter**:
  - One-click transformations (Make Shorter, More Formal, More Apologetic, Add Technical Details) or custom instructions.
- **Supporting Proof Documents**:
  - Generate official-style Medical Clinic Certificates, Roadside Tow Invoices, Transit Interruption Slips, Utility Work Orders, and Formal Absence Statements.
  - Printable / PDF-ready formatting (`window.print()`).
- **History & Archive**:
  - Full-text search, recipient/type filters, favorite star toggles, 1-click clipboard copy, and deletion.
- **Favorites**:
  - Instant access to starred explanations and documents.
- **Profile & Settings**:
  - Profile customization, generation default presets, Dark/Light theme toggle, optional Gemini API Key, and password update.

---

## 🛠️ Quick Start

### 1. Launch Server
```bash
python run.py
```
Or run directly:
```bash
.venv\Scripts\python.exe app.py
```

### 2. Access Web Interface
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🧪 Run Automated Tests
```bash
.venv\Scripts\python.exe test_app.py
```
