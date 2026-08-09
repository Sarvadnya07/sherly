# Setup & Installation Guide

This guide provides detailed instructions on how to set up Sherly for local development and usage.

## 🛠️ Environment Prerequisites

- **OS:** Windows 10/11, macOS (Apple Silicon recommended), or Linux (Ubuntu 20.04+)
- **Python:** Version 3.10 or higher
- **Git:** Installed and available in PATH
- **Ollama:** Installed and running locally

## 📦 Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Sarvadnya07/sherly.git
   cd sherly
   ```

2. **Create a Virtual Environment**
   It is highly recommended to isolate dependencies.
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `faster-whisper` and `PySide6` are large packages and may take some time to download.*

4. **Pull an Ollama Model**
   Sherly needs a local model to fall back on when deterministic logic isn't enough. We recommend Llama 3 for general use.
   ```bash
   ollama pull llama3
   ```

## 🚀 Running Sherly

Run the main entry point:
```bash
python main.py
```
This will initialize the dependency check, connect to Ollama, and launch the PySide6 UI.

## 🔧 Troubleshooting

### Audio / Microphone Issues
- **Windows:** Ensure your default recording device is correctly set in Sound Settings. `sounddevice` relies on the OS default.
- **macOS:** You may be prompted to grant Terminal/Python access to the microphone. Ensure you allow this in `System Settings > Privacy & Security > Microphone`.

### "Ollama Not Connected" Warning
If you see this on startup:
1. Verify Ollama is running (`ollama serve` or via the desktop app).
2. Check if it's running on the default port (`localhost:11434`). If not, set the `OLLAMA_URL` in your `.env`.

### PySide6 High DPI Issues (Windows)
If the UI looks blurry or improperly scaled, ensure the environment variable `QT_ENABLE_HIGHDPI_SCALING=0` is being respected. This is set automatically in `main.py`, but you may need to adjust your OS display scaling.
