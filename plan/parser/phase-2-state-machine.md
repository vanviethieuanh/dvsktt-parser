# Phase 2: Core State Machine

## Project Context & Data Structure
We are building a parser for "Đại Việt Sử Ký Toàn Thư" that converts text into structured JSON using existing Python models.

The hierarchical models are:
- **Document**: The root container holding a list of `Part` objects and a global list of `NoteReference` objects.
- **Part**: Contains `Volume` objects (e.g., "Ngoại Kỷ", "Bản Kỷ").
- **Volume**: Contains `Era` objects (e.g., "Quyển I").
- **Era**: Contains `Block` objects.
- **Block**: Either a `ReignMarker` (ruler name) or a `Record` (historical text paragraph). Records belong to the most recently parsed `ReignMarker`.

## Goal: Main State Machine
Process the body text lines (from Phase 1) sequentially to build the hierarchical `Document`.

## State Machine Execution
- Iterate through the `body_lines` of each parsed page.
- Maintain counters/pointers for the current `Part`, `Volume`, `Era`, and `Block`.
- Use regex and string matching to detect structural boundaries.
- Instantiate models and append them to the current active parent.
- When lines are identified as Records, instantiate a `Record` block.

## Structural Detection Rules

### Part
- **Detection**: Lines starting with `Đại Việt Sử Ký` and ending with `Toàn Thư` or `Thực Lục`, *excluding* lines that contain hyphens (`-`) which are page headers.
- **Fallback**: If not found before a Volume, create an implicit Part.

### Volume
- **Detection**: Lines exactly matching `Quyển` followed by Roman numerals (e.g., `Quyển I`).

### Era
- **Detection**: Lines starting with `Kỷ ` followed by title-cased words (e.g., `Kỷ Hồng Bàng Thị`).
- **Disambiguation**: An Era line will *not* contain a comma `,` or bracket `[` immediately after the Can Chi name. If it matches `^Kỷ (Hợi|Tỵ|Sửu|Mùi|Mão|Dậu)[,\[]`, it is a Record, not an Era.

### ReignMarker
- **Detection**: Short lines (< 50 characters) that are mostly Title Cased (excluding numbers/footnote markers) with no trailing punctuation like periods or commas.
- **Edge Cases**: If a `Record` appears in an `Era` before any `ReignMarker`, create an orphan/placeholder `ReignMarker` (e.g., `ReignMarker("Unknown/Placeholder")`) and append the Record to it.
- **Ambiguity Handling**: Title Case check without trailing punctuation is robust for names. Misclassified short records do minimal damage. Do not build complex NLP rules.

### Record
- **Detection**: Any body text line that does not match Part, Volume, Era, or ReignMarker. Includes chronological entries and woodblock markers like `[1a]`.
- **Handling**: Treat every distinct paragraph (non-empty line) that doesn't match a header as a distinct `Record`. Let minor text conversion typos remain to preserve original text.

## Output Expectations
- **Functions**: `parse_document(pages)` in `src/dvsktt_parser/parser.py`.
- **Expected Result**: A fully populated `Document` object containing the hierarchical structure (without linked footnotes yet).