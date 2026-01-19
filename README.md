# 🧠 Smart Attendance System

A scalable, modular, and performance-optimized web-based attendance tracking system. Built with **Streamlit**, **Supabase**, and **LangChain**, it offers role-based panels for Admins and Students with real-time syncing and AI-powered insights.

---

## 🏗️ Architecture

The project follows a clean **Service-Oriented Architecture (SOA)**:

```text
Attendence/
├── components/          → UI Layer (Streamlit Views)
│   ├── admin_ui.py      → Admin Dashboard
│   ├── student_ui.py    → Student Portal & Dashboard
│   ├── analytics_ui.py  → High-level Analytics & Charts
│   └── chatbot_ui.py    → AI Chat Interface
│
├── services/            → Business Logic Layer
│   ├── attendance_service.py → Core attendance operations
│   ├── class_service.py      → Class management (CRUD)
│   ├── chatbot_service.py    → AI Agent logic (LangGraph)
│   ├── auth_service.py       → Authentication
│   └── github_service.py     → Data export/sync
│
└── core/                → Utilities & Configuration
    ├── clients.py       → Database & API Clients (Cached)
    ├── config.py        → Env vars
    └── logger.py        → Logging
```

---

## 🚀 Key Features

### 🔐 Admin Panel
> Run via: `streamlit run admin_main.py`

*   **Class Management**: Create, delete, and manage classes.
*   **Live Controls**: Open/Close attendance instantly.
*   **Analytics Dashboard**:
    *   High-level metrics (Total Students, Average Attendance).
    *   Interactive charts (Donut Chart, Bar Graph).
    *   Top/Bottom performing students.
*   **AI Chatbot**: Query attendance data using natural language (e.g., *"Who has less than 75% attendance?"*).
*   **Data Export**: 1-click export to CSV or push specifically to GitHub.

### 🎓 Student Portal
> Run via: `streamlit run student_main.py`. Note: The student panel auto-refreshes to show new classes.

*   **Secure Submission**: Mark attendance only when a class is **Open**.
*   **Visual Dashboard**:
    *   **Live Sync**: "Refresh" button to fetch the latest class status.
    *   **Personal Analytics**: Donut chart showing "Present vs Absent" %.
    *   **History**: Detailed table of all past attendance records.
*   **Validation**: Prevents duplicate entries and verifies attendance codes.

---

## ⚡ Performance Optimizations

*   **Intelligent Caching**: Database connections and heavy queries are cached (`st.cache_resource`, `st.cache_data`) for instant UI response.
*   **Auto-Invalidation**: Caches clear automatically when data changes (e.g., opening a class, submitting attendance), ensuring *fresh* data without manual reloads.

---

## 🛠️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/smart-attendance.git
    cd smart-attendance
    ```

2.  **Install Dependencies**
    Using `uv` (recommended) or `pip`:
    ```bash
    uv venv venv
    uv pip install -e .
    ```

3.  **Environment Variables**
    Create a `.env` file (or use Streamlit secrets):
    ```ini
    SUPABASE_URL=your_url
    SUPABASE_KEY=your_key
    GITHUB_TOKEN=your_token
    GOOGLE_API_KEY=your_gemini_key
    ```

4.  **Run the Applications**
    *   **Admin**: `streamlit run admin_main.py`
    *   **Student**: `streamlit run student_main.py`

---

## ⚙️ Tech Stack

| Layer | Technology | Usage |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | Responsive UI Components |
| **Database** | Supabase | Real-time structured data |
| **Logic** | Python 3.10+ | Core Application Logic |
| **AI** | LangChain + Gemini | Data Analysis Chatbot |
| **Viz** | Matplotlib | Custom Analytics Charts |
