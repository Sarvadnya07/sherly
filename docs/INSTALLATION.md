# Sherly AI — Clean-Machine Installation Guide (Phase 14)

**Target Platforms**: Windows 10/11 (Primary Runtime Verified), Linux / macOS (CI Verified)  
**Supported Runtime**: Python 3.10+ (tested on Python 3.13), Node.js 18+ (tested on Node.js 20/26)  

---

## 1. Prerequisites

1. **Python 3.10+**: Ensure Python is installed and added to `PATH`.
2. **Node.js 18+ & npm**: Required for frontend development or custom builds.
3. **Local LLM Runner (Optional but Recommended)**:
   - Install [Ollama](https://ollama.com).
   - Pull recommended model:
     ```bash
     ollama pull qwen2.5-coder:3b
     ```

---

## 2. Quickstart Installation

### Step 1: Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/Sarvadnya07/sherly.git
cd sherly

# Create virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Setup Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 4: Launch Sherly
```bash
python main.py
```
- The backend FastAPI server starts on `http://127.0.0.1:8000`.
- The modern React desktop interface launches automatically.

---

## 3. Configuration & Cloud Keys (Optional)

Copy the configuration template:
```bash
cp config.json.example config.json
```
Edit `config.json` or `.env` with your API keys (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`).
If no cloud keys are provided, Sherly seamlessly uses local Ollama models (`qwen2.5-coder:3b` in auto mode).
