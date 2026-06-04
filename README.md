# pdfocr

Uno script Python per eseguire l'OCR su file PDF, all'interno di un virtual environment.

## Prerequisiti

Il motore OCR **Tesseract** deve essere installato sul sistema:

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# macOS (Homebrew)
brew install tesseract

# Lingue aggiuntive (es. italiano)
sudo apt install tesseract-ocr-ita   # Ubuntu/Debian
brew install tesseract-lang           # macOS
```

## Installazione

```bash
# Clona il repository (se non l'hai già fatto)
git clone https://github.com/horridus/pdfocr.git
cd pdfocr

# Crea il virtual environment e installa le dipendenze
bash setup.sh

# Attiva il virtual environment
source venv/bin/activate
```

## Utilizzo

```
python pdfocr.py <file.pdf> [<file2.pdf> ...] [-o DIR] [-l LANG] [--dpi DPI]
```

### Argomenti

| Argomento | Descrizione |
|-----------|-------------|
| `FILE.pdf` | Uno o più file PDF su cui eseguire l'OCR (obbligatorio) |
| `-o DIR`, `--output-dir DIR` | Salva il testo estratto in file `.txt` nella cartella specificata. Se omesso, l'output viene stampato su stdout. |
| `-l LANG`, `--language LANG` | Codice lingua Tesseract (default: `eng`). Usa `+` per combinare più lingue, es. `ita+eng`. |
| `--dpi DPI` | Risoluzione per il rendering delle pagine PDF (default: `300`). |

### Esempi

```bash
# OCR di un singolo file, output su stdout
python pdfocr.py documento.pdf

# OCR con lingua italiana, output in una cartella
python pdfocr.py documento.pdf -l ita -o output/

# OCR di più file con risoluzione maggiore
python pdfocr.py file1.pdf file2.pdf --dpi 400 -o output/
```

## Dipendenze Python

Le dipendenze sono definite in `requirements.txt`:

- [pdf2image](https://github.com/Belval/pdf2image) – converte le pagine PDF in immagini
- [pytesseract](https://github.com/madmaze/pytesseract) – wrapper Python per Tesseract OCR
- [Pillow](https://python-pillow.org/) – elaborazione delle immagini