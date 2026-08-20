# Sherly AI — Complete Environment Setup & Troubleshooting Guide

**Target Version**: 2.0.0  

---

## 1. System Requirements

- **Operating System**: Windows 10/11 (Primary Runtime Verified), macOS 12+, Ubuntu 22.04+
- **Python**: Version 3.10 to 3.13 (Python 3.13 recommended)
- **Node.js**: Version 18.x or 20.x LTS
- **RAM**: Minimum 8GB (16GB recommended for local 7B models)
- **Hardware**: Dedicated microphone for voice commands (optional)

---

## 2. Installation Steps

### Step 1: Clone & Python Environment
```bash
git clone https://github.com/Sarvadnya07/sherly.git
cd sherly

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Build Frontend Assets
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 3: Local Model Setup (Ollama)
```bash
# In a separate terminal:
ollama serve
ollama pull qwen2.5-coder:3b
```

### Step 4: Run Application
```bash
python main.py
```

---

## 3. Common Troubleshooting

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `Ollama connection refused` | Ollama daemon not running. | Run `ollama serve` or configure cloud API keys. |
| `Port 8000 in use` | Background process holding port 8000. | Set `SHERLY_PORT=8080` in environment. |
| `No module named sounddevice` | Missing PortAudio libraries on Linux. | Run `sudo apt install libportaudio2`. |
