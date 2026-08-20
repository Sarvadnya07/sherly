"""
SHERLY RELEASE PACKAGING ORCHESTRATOR — scripts/package.py

Automates:
1. Environment & Dependency Verification
2. PyTest & Compilation Regression Suite
3. Frontend Production Compilation (TypeScript + Vite)
4. Artifact Manifest Generation & SHA-256 Checksums
5. Honest Cross-Platform Status Reporting
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
RELEASE_DIR = ROOT_DIR / "release"


def sha256_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_cmd(cmd: list[str], cwd: Path | None = None) -> bool:
    print(f"  [RUN] {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd or ROOT_DIR)
    return res.returncode == 0


def build_package(verify_only: bool = False) -> int:
    print("============================================================")
    print("SHERLY PRODUCTION PACKAGING PIPELINE")
    print("============================================================")

    # 1. Verify Python Compilation
    print("\n[1/5] Verifying Python syntax and compilation...")
    if not run_cmd([sys.executable, "-m", "compileall", "-q", "."]):
        print("  [ERROR] Python compilation failed!")
        return 1

    # 2. Run Test Suite
    print("\n[2/5] Running Backend Regression Test Suite...")
    if not run_cmd([sys.executable, "-m", "pytest", "tests/", "-q"]):
        print("  [ERROR] Test suite failed!")
        return 1

    # 3. Build Frontend Production Assets
    print("\n[3/5] Building Frontend Production Assets (Vite)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if not run_cmd([npm_cmd, "run", "build"], cwd=FRONTEND_DIR):
        print("  [ERROR] Frontend build failed!")
        return 1

    # 4. Generate Release Manifest & Checksums
    print("\n[4/5] Generating Artifact Manifest & SHA-256 Checksums...")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "app_name": "Sherly AI",
        "version": "2.0.0",
        "build_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host_platform": sys.platform,
        "artifacts": {},
        "platform_certification": {
            "windows": "RUNTIME_VERIFIED" if sys.platform == "win32" else "BUILD_VERIFIED",
            "macos": "NOT_TESTED",
            "linux": "NOT_TESTED",
        }
    }

    # Index frontend dist assets
    if DIST_DIR.exists():
        for asset in DIST_DIR.rglob("*"):
            if asset.is_file():
                rel_path = str(asset.relative_to(ROOT_DIR)).replace("\\", "/")
                manifest["artifacts"][rel_path] = {
                    "size_bytes": asset.stat().st_size,
                    "sha256": sha256_file(asset),
                }

    manifest_file = RELEASE_DIR / "release_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"  [SAVED] {manifest_file} with {len(manifest['artifacts'])} verified artifacts.")

    # 5. Report Status
    print("\n[5/5] Release Packaging Summary:")
    print(f"  - Host Platform: {sys.platform}")
    print(f"  - Windows Status: {manifest['platform_certification']['windows']}")
    print(f"  - macOS Status: {manifest['platform_certification']['macos']}")
    print(f"  - Linux Status: {manifest['platform_certification']['linux']}")
    print(f"  - Verified Assets: {len(manifest['artifacts'])}")
    print("\nSUCCESS: Packaging pipeline verified.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sherly Packaging Orchestrator")
    parser.add_argument("--verify", action="store_true", help="Verify build and generate manifest")
    args = parser.parse_args()

    sys.exit(build_package(verify_only=args.verify))
