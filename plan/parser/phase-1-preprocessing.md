# Phase 1: Page Preprocessing

## Project Context & Data Structure
We are building a parser for "Đại Việt Sử Ký Toàn Thư" that converts text (extracted from a selectable PDF) into structured JSON using existing Python models. 

The hierarchical models are:
- **Document**: The root container holding a list of `Part` objects and a global list of `NoteReference` objects.
- **Part**: Contains `Volume` objects (e.g., "Ngoại Kỷ", "Bản Kỷ").
- **Volume**: Contains `Era` objects (e.g., "Quyển I").
- **Era**: Contains `Block` objects.
- **Block**: Either a `ReignMarker` (ruler name) or a `Record` (historical text paragraph).
- **NoteReference**: Links a footnote definition to a specific location (`pos`) in a `Block`.

## Goal: Page Preprocessor
Read the raw text, split it by page, and yield clean structures separating body text and footnotes.

## Implementation Details
1. **Split by Page**: Read the entire text and split it by the form-feed character (`\x0c` or `\f`). Each chunk represents a physical page.
2. **Page Preprocessing**:
   - Remove page headers (e.g., `Đại Việt Sử Ký Toàn Thư - Ngoại Kỷ - Quyển I`) and page numbers.
   - Separate the page into **Body Text** and **Footnote Definitions** by scanning from the bottom up for footnote patterns.
   - *Page Information*: The original physical page numbers (e.g., `3`) and woodblock leaf markers (e.g., `[1a]`, `[12b]`) are present. Woodblock leaf markers belong to the text itself and must be preserved verbatim in the `Record` text.

## Footnote Definition Pattern
At the bottom of a page, footnotes follow a strict pattern: a line with just a number (`^\d+$`), followed by an empty line, followed by the note text (which may span multiple lines until the next number or end of page).

## Output Expectations
- **Files**: Create `src/dvsktt_parser/parser.py`.
- **Functions**: `split_pages(text)`, `parse_page_content(page_string)`.
- **Expected Result**: A list of parsed pages, where each page has a list of body strings and a dictionary mapping footnote numbers to text definitions.