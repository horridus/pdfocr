#!/usr/bin/env python3
"""
pdfocr.py - Perform OCR on PDF files and extract text.

Usage:
    python pdfocr.py <file.pdf> [<file2.pdf> ...] [-o output_dir] [-l lang]

Requirements:
    - Tesseract OCR must be installed on the system
    - Python dependencies listed in requirements.txt
"""

import argparse
import os
import sys

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    print(
        f"Error: missing dependency: {e}\n"
        "Run 'pip install -r requirements.txt' inside the virtual environment.",
        file=sys.stderr,
    )
    sys.exit(1)


def ocr_pdf(pdf_path: str, output_dir: str | None, language: str, dpi: int) -> str:
    """Convert a PDF to images page by page and run Tesseract OCR on each page.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory where the .txt result will be saved.
                    If None, text is printed to stdout.
        language: Tesseract language code (e.g. 'ita', 'eng').
        dpi: Resolution used when rendering PDF pages to images.

    Returns:
        The full extracted text.
    """
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        return ""

    print(f"Processing: {pdf_path}", file=sys.stderr)

    try:
        pages = convert_from_path(pdf_path, dpi=dpi)
    except Exception as exc:
        print(f"Error converting PDF to images: {exc}", file=sys.stderr)
        return ""

    page_texts: list[str] = []
    for i, page_image in enumerate(pages, start=1):
        print(f"  OCR page {i}/{len(pages)}...", file=sys.stderr)
        text = pytesseract.image_to_string(page_image, lang=language)
        page_texts.append(text)

    full_text = "\n\f\n".join(page_texts)  # form-feed between pages

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_path = os.path.join(output_dir, f"{base}.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(full_text)
        print(f"Saved: {out_path}", file=sys.stderr)
    else:
        print(full_text)

    return full_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perform OCR on one or more PDF files using Tesseract.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "pdfs",
        nargs="+",
        metavar="FILE.pdf",
        help="PDF file(s) to process.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory where .txt output files will be saved. "
        "If omitted, text is printed to stdout.",
    )
    parser.add_argument(
        "-l",
        "--language",
        default="eng",
        metavar="LANG",
        help="Tesseract language code (default: eng). "
        "Use '+' to combine multiple languages, e.g. 'ita+eng'.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        metavar="DPI",
        help="Resolution for rendering PDF pages (default: 300).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    for pdf in args.pdfs:
        ocr_pdf(
            pdf_path=pdf,
            output_dir=args.output_dir,
            language=args.language,
            dpi=args.dpi,
        )


if __name__ == "__main__":
    main()
