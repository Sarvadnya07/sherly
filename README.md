# 👩‍💻 Sherly AI - Desktop Assistant

Sherly is a powerful, desktop-native AI assistant designed to integrate seamlessly into your workflow. It combines voice-first interaction with local-first AI processing to provide a secure, fast, and feature-rich assistant experience.

Sherly is built for developers and power users who want an assistant that can control their system, answer complex questions, and even explain code—all from a simple tray icon and voice commands.

---

## 🚀 Key Features

### 🎙️ Voice-First Interaction
- **Advanced STT**: Powered by `faster-whisper` for near-instant, high-accuracy local voice transcription.
- **Smart Filtering**: Integrated high-pass filtering (using `scipy`) to remove background fan noise and hum before transcription.
- **Natural TTS**: Uses `pyttsx3` for clear, local voice responses with adjustable speech rates.

### 🧠 Local AI Intelligence
- **Ollama Integration**: Natively connects to a local Ollama server (defaults to the `mistral` model) for private, offline-capable AI responses.
- **Intent-Based Routing**: Sherly identifies whether you're asking a question, commanding the system, or need a web search.
- **Web Search**: Automatically intelligently detects when a query needs external data and searches the web using DuckDuckGO for real-time information.

### 🛠️ Developer Tools
- **Code Explanation**: Select any block of code and ask "Explain this code." Sherly will automatically copy it to the clipboard and provide a detailed logic breakdown.
- **Modular Design**: Structured as a modular Python package with clean separation between AI, commands, core loop, and UI.

### 💻 System Automation
- **App Control**: Launch Chrome and VS Code via voice.
- **Web Navigation**: Open GitHub, ChatGPT, Google, and YouTube instantly.
- **System Commands**: Lock your computer, open the Downloads folder, or trigger a system shutdown.

---

## 🛠️ Tech Stack

- **Core Logic**: Python 3.10+
- **Voice Recognition**: `faster-whisper` (Base model for CPU efficiency)
- **Speech Synthesis**: `pyttsx3`
- **AI Engine**: [Ollama](https://ollama.com/) (Mistral)
- **Signal Processing**: `scipy` (High-pass filters)
- **UI Framework**: `pystray` (System Tray Icon)
- **Utilities**: `pyautogui`, `pyperclip`, `duckduckgo-search`, `mss`, `sounddevice`

---

## 📦 Project Structure

Sherly follows a clean, modular architecture:

```bash
sherly/
├── sherly_ai/         # AI models & prompts
├── sherly_commands/   # System, Web, & Developer automation
├── sherly_core/       # Core loop, STT (with filtering), & routing
├── sherly_ui/         # System tray implementation
├── sherly_utils/      # Screen, Clipboard, & File helpers
├── config/            # Project configurations
├── main.py            # Startup handler
└── requirements.txt   # Dependency list
```

---

## ⚙️ Installation & Setup

1. **Clone the project**:
   ```bash
   git clone https://github.com/yourusername/sherly.git
   cd sherly
   ```

2. **Set up Ollama**:
   - Install [Ollama](https://ollama.com/)
   - Pull the Mistral model:
     ```bash
     ollama pull mistral
     ```
   - Ensure the Ollama server is running (usually on `http://localhost:11434`).

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: For Windows, ensure standard portaudio-related DLLs are present. For Linux, you may need `sudo apt install libportaudio2`).*

4. **Run Sherly**:
   ```bash
   python main.py
   ```

---

## 🎯 Usage

1. **Start Sherly**: Click the tray icon and select "Start Sherly."
2. **Commands**: Once Sherly is listening, try:
   - *"Open GitHub"* — Opens GitHub in your browser.
   - *"What is the latest score in Formula 1?"* — Triggers an intelligent web search.
   - *"Explain this code"* — Automatically reads code from your clipboard/selected text.
   - *"Lock my computer"* — Locks Windows immediately.
3. **Exit**: Right-click the tray icon and select "Exit."

---

## 📝 License

This project is open-source and available under the **MIT License**.
