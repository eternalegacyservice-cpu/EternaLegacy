#!/usr/bin/env bash
#
# Universal Secure Git Setup (v1.1 - EternaLegacy Optimized)
# Works: macOS, Linux, Windows (Git Bash)
#

# Stop on first error
set -e

echo ""
echo "Secure Git Setup (Cross-Platform)"
echo "------------------------------------"

# Detect platform
OS="$(uname -s)"
# Default values for Linux/macOS
ACTIVATE=".venv/bin/activate"
PY="python3"
SEP="/"
# Override for Windows (Git Bash)
if [[ "$OS" == *"NT"* ]] || [[ "$OS" == *"MINGW"* ]]; then
  ACTIVATE=".venv/Scripts/activate"
  PY="python"
  SEP="\\"
fi

# Ensure python exists
if ! command -v $PY >/dev/null 2>&1; then
  echo "Warning: $PY not found. Trying fallback 'python'..."
  PY="python"
  if ! command -v $PY >/dev/null 2>&1; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
  fi
fi

# Create venv
echo "Creating virtual environment..."
$PY -m venv .venv

# Activate venv if possible
if [ -f "$ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$ACTIVATE"
  echo "Virtual environment activated."
else
  echo "Warning: Could not auto-activate .venv. Please activate it manually."
fi

# --- UPGRADE POINT: Install tools & requirements ---
echo "Installing core dependencies & security tools..."

# 1. Upgrade pip
# pip install --upgrade pip >/dev/null

# 2. Install pre-commit tools
pip install pre-commit detect-secrets >/dev/null

# 3. Install core dependencies
pip install \
  fastapi uvicorn python-dotenv requests \
  python-jose[cryptography] bcrypt cryptography \
  web3 psycopg2-binary stripe google-genai \
  >/dev/null

echo "All dependencies installed."

# --- Generate .gitignore if not exist ---
if [ ! -f ".gitignore" ]; then
  echo "Creating .gitignore (EternaLegacy Optimized) ..."
  # Updating .gitignore for project structure
  cat > .gitignore << 'EOF'
# === Secrets & Credentials (EternaLegacy) ===
.env
.env.*
*.pen
*.key
*.p12
*.jks
id_rsa*
service-account*.json

# Vault Agent uses these keys
# The keys themselves are in .env, but ensure any backups are ignored
recovery/vault_keys/


# === Python ===
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# === OS ===
.DS_Store
Thumbs.db
desktop.ini

# === IDE ===
.idea/
.vscode/
*.iml
*.iws
*.ipr
nbproject/
*.swp
*~

# === EternaLegacy Specific ===
approvals/
data/
logs/
outbox/
reports/
EOF
  echo ".gitignore created successfully."
fi

# --- Setup pre-commit hooks ---
if [ ! -f ".pre-commit-config.yaml" ]; then
  echo "Creating .pre-commit-config.yaml ..."
  cat > .pre-commit-config.yaml << 'EOF'
# EternaLegacy Pre-Commit Configuration
# See https://pre-commit.com for more information

repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
  - id: detect-secrets
    args: ['--baseline', '.secrets.baseline']
EOF
fi

echo "Setting up pre-commit hooks..."
pre-commit install
echo "Pre-commit hooks installed."

echo "------------------------------------"
echo "✅ Secure Git setup complete."
echo "------------------------------------"
