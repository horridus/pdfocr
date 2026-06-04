#!/usr/bin/env python3
"""
format_text.py - Reformat OCR-extracted text for better readability.

Usage:
    python format_text.py <input.txt> <output.txt>

The script:
  1. Removes OCR noise lines (low alphabetic content, page artefacts)
  2. Removes repeated "Ars Magica Fifth Edition" header/footer lines
  3. Joins hyphenated word-breaks across lines
  4. Reflows paragraph text (joins wrapped lines into full paragraphs)
  5. Normalises whitespace and section separators
"""

import re
import sys
import textwrap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def alpha_ratio(s: str) -> float:
    """Fraction of characters in *s* that are alphabetic."""
    if not s:
        return 0.0
    return sum(1 for c in s if c.isalpha()) / len(s)


def is_noise_line(line: str) -> bool:
    """Return True if the line appears to be an OCR artefact / noise."""
    s = line.strip()
    if not s:
        return False
    # Very short lines with no real words (up to 4 chars)
    if len(s) <= 4:
        return True
    # Lines that are mostly non-alphabetic (symbols, numbers, punctuation noise)
    if alpha_ratio(s) <= 0.25 and len(s) < 80:
        return True
    # Running page header / footer: contains "Magica" and some form of "Edition"
    if re.search(r'[Mm]agica\s+Fifth', s):
        return True
    # OCR garbage patterns: lots of mixed special characters
    if re.search(r'[_\\|{}[\]<>@#$%^&*~`]{2,}', s):
        return True
    # Lines delimited by pipe characters (table artefacts / sidebar noise)
    if s.startswith('|') or s.endswith('|'):
        return True
    # Short ALL-CAPS or mixed-case tokens that are clearly not words
    # (e.g. "LRMEC TES", "ns fF", "ibertisrcatange") – short, no common English structure
    if len(s) <= 20 and alpha_ratio(s) > 0.6:
        words = s.split()
        # Exclude lines with common English words
        if not re.search(r'(?i)\b(the|and|or|of|in|to|a|an|is|it|he|she|we|for|are|at|by|do'
                         r'|die|all|one|two|may|can|has|had|his|her|its|not|but|yet|no|so)\b', s):
            all_short = all(len(w) <= 6 for w in words)
            if all_short and len(words) <= 4:
                # Check for words with very low vowel content (likely abbreviations or noise)
                def word_vowel_ratio(w: str) -> float:
                    return sum(1 for c in w.lower() if c in 'aeiou') / max(1, len(w))
                low_vowel_words = sum(1 for w in words if word_vowel_ratio(w) < 0.25)
                if low_vowel_words >= len(words) - 1:  # most words have few vowels
                    return True
    # Single-word lines that look like OCR garbage (long, no vowel runs, no spaces)
    if ' ' not in s and len(s) > 10:
        vowels = sum(1 for c in s.lower() if c in 'aeiou')
        if vowels / len(s) < 0.15:  # very few vowels → likely garbage
            return True
    return False


def is_heading(line: str) -> bool:
    """Return True if the line looks like a section heading."""
    s = line.strip()
    # Explicit chapter markers
    if re.match(r'(?i)^(chapter|appendix)\s+(one|two|three|four|five|six|seven|eight|nine|ten'
                r'|eleven|twelve|thirteen|fourteen|fifteen|i{1,3}|iv|v|vi{0,3}|ix|xi{0,2}|xiv|xv'
                r'|\d+)', s):
        return True
    # ALL-CAPS short lines (3-7 words)
    words = s.split()
    if 1 <= len(words) <= 8 and s == s.upper() and alpha_ratio(s) > 0.5:
        return True
    # Title-case short lines (section headers)
    if 1 <= len(words) <= 6 and re.match(r'^[A-Z]', s) and not s.endswith(','):
        # Not a normal sentence start (check against sentence-like length)
        if len(s) < 50 and not re.search(r'\s{2,}', s):
            pass  # may be heading – handled by caller via blank-line context
    return False


SENTENCE_END = re.compile(r'[.!?:;""\')\]]\s*$')
HYPHEN_BREAK = re.compile(r'-\s*$')


def clean_page(page_text: str) -> list[str]:
    """
    Clean a single OCR page: remove noise lines and return cleaned lines.
    """
    lines = page_text.split('\n')
    result = []
    for line in lines:
        stripped = line.rstrip()
        if is_noise_line(stripped):
            # Replace with blank to preserve paragraph gaps
            result.append('')
        else:
            result.append(stripped)
    return result


def join_hyphenated(lines: list[str]) -> list[str]:
    """Join lines where a word is hyphenated at end of line.

    Handles chained hyphens (a join may produce a new line that itself ends
    with a hyphen) by re-checking the just-joined line in a nested loop.
    Also looks past up to MAX_SKIP blank lines to find the continuation word
    (OCR artefacts sometimes insert blank lines in the middle of a split word).
    """
    MAX_SKIP = 12  # max blank lines to skip when searching for continuation
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Greedily consume as many chained hyphen-continuations as possible
        while HYPHEN_BREAK.search(line):
            # Look ahead, skipping blank lines, for a lowercase continuation
            skip = 1
            while i + skip < len(lines) and not lines[i + skip].strip():
                skip += 1
                if skip > MAX_SKIP:
                    break
            if i + skip >= len(lines):
                break
            next_line = lines[i + skip].lstrip()
            if next_line and next_line[0].islower():
                # Consume all skipped blank lines and the continuation line
                line = line.rstrip().rstrip('-') + next_line
                i += skip  # advance past blanks + continuation
            else:
                break
        out.append(line)
        i += 1
    return out


def reflow_paragraphs(lines: list[str]) -> list[str]:
    """
    Merge wrapped lines that belong to the same paragraph.

    The primary boundary between paragraphs is a blank line.  Within a
    paragraph block (consecutive non-blank lines), all lines are joined into
    a single line unless a line looks like a standalone heading or label.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Blank line: pass through
        if not line.strip():
            out.append(line)
            i += 1
            continue

        # Start accumulating a paragraph block (runs until a blank line)
        block = [line.rstrip()]
        i += 1
        while i < len(lines) and lines[i].strip():
            block.append(lines[i].rstrip())
            i += 1

        if len(block) == 1:
            out.append(block[0])
        else:
            # Split the block at natural sub-boundaries:
            # Lines ending with sentence-final punctuation start a new output line.
            # This preserves list items and short standalone lines.
            current: list[str] = []
            for part in block:
                s = part.strip()
                if not s:
                    continue
                # If the current accumulation is very short (< 30 chars) and
                # this part starts with a capital, flush and start fresh.
                if current and len(' '.join(current)) < 30 and re.match(r'^[A-Z*•]', s):
                    out.append(' '.join(p.strip() for p in current))
                    current = [part]
                else:
                    current.append(part)
                # Flush after a sentence-ending line that is reasonably complete
                prev_joined = ' '.join(p.strip() for p in current)
                if SENTENCE_END.search(part.rstrip()) and len(prev_joined) > 40:
                    out.append(prev_joined)
                    current = []
            if current:
                out.append(' '.join(p.strip() for p in current))

    return out


def collapse_blank_lines(lines: list[str], max_blank: int = 1) -> list[str]:
    """Collapse runs of blank lines to at most *max_blank* blank lines."""
    out: list[str] = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= max_blank:
                out.append('')
        else:
            blank_count = 0
            out.append(line)
    return out


def add_section_separators(lines: list[str]) -> list[str]:
    """Add visual separators before chapter/appendix headings."""
    out: list[str] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r'(?i)^(chapter|appendix)\s+\w+', s):
            # Insert separator if not already preceded by one
            if out and out[-1] != ('=' * 72):
                out.append('')
                out.append('=' * 72)
        out.append(line)
    return out


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def format_file(input_path: str, output_path: str) -> None:
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into pages
    pages = content.split('\f')

    all_lines: list[str] = []
    for page in pages:
        cleaned = clean_page(page)
        all_lines.extend(cleaned)
        # Ensure at least one blank line between pages
        if all_lines and all_lines[-1] != '':
            all_lines.append('')

    # Join hyphenated word breaks
    all_lines = join_hyphenated(all_lines)

    # Reflow paragraphs
    all_lines = reflow_paragraphs(all_lines)

    # Collapse excessive blank lines
    all_lines = collapse_blank_lines(all_lines, max_blank=2)

    # Add visual section separators
    all_lines = add_section_separators(all_lines)

    # Final trailing newline
    output = '\n'.join(all_lines).rstrip('\n') + '\n'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Written {len(output.splitlines())} lines to {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.txt> <output.txt>", file=sys.stderr)
        sys.exit(1)
    format_file(sys.argv[1], sys.argv[2])
