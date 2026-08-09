# Deployment & Packaging Guide

Since Sherly is a desktop-native application, "deployment" refers to packaging the Python application into a standalone executable for end-users, rather than deploying it to a web server.

## 📦 Packaging with PyInstaller

To distribute Sherly without requiring users to install Python and configure virtual environments, we use `PyInstaller`.

### Prerequisites
Make sure your virtual environment is active and all dependencies are installed.

```bash
pip install pyinstaller
```

### Build Instructions

To build a standalone executable:

```bash
# Windows
pyinstaller --name "SherlyAI" --windowed --icon=src/sherly/ui/assets/sherlyai.ico main.py

# macOS
pyinstaller --name "SherlyAI" --windowed --icon=src/sherly/ui/assets/sherlyai.icns main.py
```

- `--windowed`: Hides the console window on startup (critical for desktop apps).
- `--icon`: Sets the application icon.

The compiled executable will be located in the `dist/` directory.

## 🐳 Docker Deployment (Sandboxing)

While Sherly runs natively on the host to interact with your IDE and files, it can utilize Docker to create an isolated execution sandbox for *running* dangerous code.

If you are deploying a dedicated Sherly worker in a CI/CD pipeline:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run headless without PySide6 UI
CMD ["python", "main.py", "--headless"]
```

## 🔄 CI/CD Recommendations

For future continuous integration:
1. **Linting:** Use GitHub Actions to run `ruff` on all PRs.
2. **Testing:** Run `pytest` on Linux, macOS, and Windows runners.
3. **Releases:** Use GitHub Actions to automatically trigger a `PyInstaller` build and attach the compiled binaries to GitHub Releases when a new tag is pushed.
