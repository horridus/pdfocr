#!/usr/bin/env bash
# setup.sh - Create a Python virtual environment and install dependencies.
# Usage: bash setup.sh

set -euo pipefail

VENV_DIR="venv"

echo "Creating virtual environment in './${VENV_DIR}'..."
python3 -m venv "${VENV_DIR}"

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment run:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "Then run OCR on a PDF with:"
echo "  python pdfocr.py <file.pdf>"
echo ""
echo "NOTE: Tesseract OCR must be installed on your system."
echo "  Ubuntu/Debian:  sudo apt install tesseract-ocr"
echo "  macOS (Homebrew): brew install tesseract"
