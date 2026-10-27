# CivicFlow – Smart Municipal Complaint Management System

CivicFlow is an AI/ML-driven municipal governance web application engineered for citizens, municipal administrators, and municipal department staff. It streamlines complaint logging, automated category classification, urgency-based priority estimation, duplicate ticket detection using TF-IDF and cosine similarity, and real-time status tracking.

---

## 🏛️ System Features & User Roles

### 1. Citizen Portal (3 Sections)
- **Home & Submit Complaint:** Intuitive submission form with live ML category prediction, priority scoring explanation, and proactive duplicate checking before ticket registration.
- **My Complaints & Status Tracking:** Complete lifecycle visibility for all tickets submitted by the citizen, including real-time status badges (`Pending`, `Assigned`, `In Progress`, `Resolved`, `Rejected`) and an immutable timestamped audit timeline.
- **Complaint Details & Feedback:** Post-resolution citizen satisfaction rating (1 to 5 stars) and feedback notes to measure civic service quality.

### 2. Municipal Administrator Portal (4 Sections)
- **Dashboard & Statistics:** Real-time city-wide KPI metrics and Plotly charts displaying complaint distribution across categories, resolution funnel stages, priority tiers, and department workloads.
- **Complaint Management & Department Assignment:** Searchable municipal registry with department reassignment, administrative status overrides, and field notes.
- **AI Review & Duplicate Detection Queue:** Triage queue flagging complaints with low classification confidence (<60%) or high TF-IDF cosine duplicate similarity (>60%), enabling administrators to verify categories, adjust priority, or merge duplicate tickets into parent records.
- **Reports & Analytics:** Filterable operational summaries with one-click CSV report export.

### 3. Department Staff Portal (2 Sections)
- **Assigned Complaints:** Strictly filtered view displaying only tickets assigned to the logged-in staff member's department (Roads, Solid Waste, Water Works, Street Lighting, Drainage, Sanitation, etc.) with priority indicators and search.
- **Update Progress & Resolution Notes:** Field crew interface to update work order status (`In Progress`, `Resolved`, `Rejected`), input mandatory operational resolution notes, and append to the audit history.

---

## 🤖 AI / Machine Learning Architecture

1. **Complaint Classification:** Built with Scikit-learn using a `TfidfVectorizer` (unigrams and bigrams, sublinear term frequency) coupled with a `MultinomialNB` classifier trained across 7 municipal categories (`potholes`, `garbage`, `streetlights`, `drainage`, `water_supply`, `sanitation`, `other`).
2. **Confidence-Based Manual Review:** If prediction confidence falls below 60%, the ticket is automatically routed to the Administrator AI Review queue.
3. **Priority Estimation Engine:** Calculates severity levels (`Low`, `Medium`, `High`, `Critical`) using hazard keywords (e.g., exposed live electrical wire, flooding, burst water main, hospital vicinity) combined with category base weights.
4. **Duplicate Detection:** Computes pairwise cosine similarity between incoming complaints and active open records via TF-IDF representations. Any match exceeding 60% similarity triggers duplicate warnings and linkage to the parent ticket.

### ⚠️ Dataset & Model Limitations
The training dataset (`data/sample_complaints.csv`) is a **synthetic demonstration dataset** created to simulate civic complaint patterns. 
- **Limitations:** Real-world municipal complaints contain colloquial phrasing, local dialect, misspellings, and multilingual input. Before deploying in real city governance, train the classifier on historical municipal records (minimum 5,000+ verified records) and evaluate domain-specific precision and recall.
- **Evaluation:** Model metrics are computed on a genuine stratified test split (25% holdout) using Scikit-learn's `accuracy_score` and `classification_report`. No accuracy metrics are fabricated.

---

## 🔒 Security & Data Persistence Notice

- **Password Security:** Passwords are never stored in plaintext. They are salted with a 128-bit unique hex salt and hashed with SHA-256.
- **Role Isolation:** Citizens cannot assign administrative or staff privileges to themselves. Staff accounts can only view and modify complaints belonging to their assigned department.
- **Demonstration Storage Warning:** The local SQLite database (`civicflow.db`) is intended for local execution and demonstration. On stateless container platforms or temporary cloud hosts (like Streamlit Community Cloud), the local filesystem is ephemeral and may reset upon container restarts. For production municipal use, connect to a managed persistent database (such as PostgreSQL) with TLS encryption, rate limiting, and SSO/OAuth.

---

## 💻 Beginner-Friendly Windows Setup Instructions

### Prerequisites
1. Install **Python 3.10 or newer** from [python.org](https://www.python.org/). Check the box **"Add Python to PATH"** during installation.
2. Install **Git for Windows** from [git-scm.com](https://git-scm.com/).

### Step 1: Open Terminal (PowerShell or Command Prompt)
Press `Win + R`, type `powershell`, and press Enter.

### Step 2: Clone or Download the Repository
```powershell
git clone https://github.com/<your-username>/civicflow.git
cd civicflow
```

### Step 3: Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If you see an execution policy error in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and retry).*

### Step 4: Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: (Optional) Train the Model
```powershell
python train_model.py
```
This generates `model.joblib` and prints true accuracy and F1 scores.

### Step 6: Launch CivicFlow
```powershell
streamlit run app.py
```
Your default web browser will automatically open to `http://localhost:8501`.

---

## 🚀 How to Push to GitHub and Deploy to Streamlit Community Cloud

### Step 1: Initialize Git and Commit
```bash
git init
git add .
git commit -m "Initial commit of CivicFlow municipal complaint system"
```

### Step 2: Push to GitHub
1. Log in to [GitHub](https://github.com/) and click **New repository**.
2. Name it `civicflow` and keep it Public. Do not initialize with README (you already have one).
3. Push your local files:
```bash
git branch -M main
git remote add origin https://github.com/<your-username>/civicflow.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Community Cloud
1. Visit [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **New app**.
3. Select your repository: `<your-username>/civicflow`.
4. Set **Branch** to `main`.
5. Set **Main file path** to `app.py`.
6. Click **Deploy!**
Streamlit will install `requirements.txt`, run `database.py` initialization, and launch the live web application.

> *Note regarding Cloud Hosting: Streamlit Community Cloud provides application hosting in accordance with their platform policies and resource limits. Review their terms and current resource guidelines when deploying.*

---

## 🔑 Default Demonstration Accounts

| Role | Username | Password | Notes |
|---|---|---|---|
| **Citizen** | `citizen1` | `citizen123` | Aarav Sharma (Downtown) |
| **Citizen** | `citizen2` | `citizen123` | Elena Rostova (Westside) |
| **Municipal Administrator** | `admin1` | `admin123` | Full city-wide oversight & triage |
| **Roads Staff** | `roads_staff` | `staff123` | Roads & Infrastructure Dept |
| **Waste Staff** | `waste_staff` | `staff123` | Solid Waste Management Dept |
| **Water Staff** | `water_staff` | `staff123` | Water Works & Supply Dept |
| **Lighting Staff** | `light_staff` | `staff123` | Electrical & Lighting Dept |
| **Drainage Staff** | `drain_staff` | `staff123` | Drainage & Stormwater Dept |
| **Sanitation Staff** | `health_staff` | `staff123` | Public Health & Sanitation Dept |

---

## 📁 Project Structure

```
civicflow/
├── app.py                      # Main entrypoint with RBAC routing & authentication
├── requirements.txt            # Python dependencies for Streamlit Cloud
├── README.md                   # Complete documentation and setup manual
├── database.py                 # SQLite schema, salt+SHA256 hashing, audit history
├── train_model.py              # Scikit-learn TF-IDF + Naive Bayes training script
├── classifier.py               # ML prediction, confidence scoring & department mapping
├── priority_engine.py          # Semantic priority and hazard estimation engine
├── duplicate_detector.py       # TF-IDF cosine similarity duplicate detector
├── data/
│   └── sample_complaints.csv   # Labelled synthetic dataset across 7 categories
└── pages/
    ├── 1_Citizen.py            # Citizen Multi-page view
    ├── 2_Municipal_Admin.py    # Administrator Multi-page view
    └── 3_Department_Staff.py   # Department Staff Multi-page view
```
