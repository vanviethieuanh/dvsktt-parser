# Parser Implementation Plan

## 1. Data Structure Understanding

The source text maps to the existing Python models as a hierarchical tree.
- **Document**: The root container for the entire text. It holds a list of `Part` objects and a global list of `NoteReference` objects.
- **Part**: The top-level division, distinguishing major sections like "Ngoại Kỷ" and "Bản Kỷ". Contains a list of `Volume` objects.
- **Volume**: A book or scroll division (e.g., "Quyển I", "Quyển II"). Contains a list of `Era` objects.
- **Era**: A chronological epoch (e.g., "Kỷ Hồng Bàng Thị", "Kỷ Nhà Thục"). Contains a list of `Block` objects.
- **Block**: The actual content. A Block can be either a `ReignMarker` (the name of a ruler, e.g., "Kinh Dương Vương") or a `Record` (a paragraph of historical text). Records belong to the most recently parsed `ReignMarker`.
- **NoteReference**: A globally stored pointer that links a footnote definition to a specific location in a `Block`. It uses indices (`part`, `volume`, `era`, `block`) to resolve the exact block, and `pos` (character index) to pinpoint the marker within that block's text.

## 2. Parsing Strategy

The parser will operate as a deterministic, line-by-line state machine combined with page-level preprocessing.

**Order of Operations:**
1. **Split by Page**: Read the entire text and split it by the form-feed character (`\x0c` or `\f`). Each chunk represents a physical page.
2. **Page Preprocessing**:
   - Remove page headers (e.g., `Đại Việt Sử Ký Toàn Thư - Ngoại Kỷ - Quyển I`) and page numbers.
   - Separate the page into **Body Text** and **Footnote Definitions** by scanning from the bottom up for footnote patterns.
3. **State Machine Execution**:
   - Iterate through the Body Text lines of each page.
   - Maintain counters/pointers for the current `Part`, `Volume`, `Era`, and `Block`.
   - Use regex and string matching (heuristics) to detect structural boundaries.
   - Instantiate models and append them to the current active parent.
   - When text lines are identified as Records, instantiate a `Record` block.
4. **Footnote Extraction**:
   - After parsing a Block's text on a given page, scan the text for footnote markers corresponding to the Footnote Definitions extracted for that page.
   - Create `NoteReference` objects and append them to `Document.notes`.

## 3. Structural Detection Rules

### Part
- **Detection**: Lines starting with `Đại Việt Sử Ký` and ending with `Toàn Thư` or `Thực Lục` (e.g., `Đại Việt Sử Ký Ngoại Kỷ Toàn Thư`), *excluding* lines that contain hyphens (`-`) which are page headers.
- **Example**: `Đại Việt Sử Ký Ngoại Kỷ Toàn Thư`
- **Fallback**: If not found before a Volume, create an implicit Part.

### Volume
- **Detection**: Lines exactly matching `Quyển` followed by Roman numerals (e.g., `Quyển I`, `Quyển II`, `Quyển XI`).
- **Example**: `Quyển I`

### Era
- **Detection**: Lines starting with `Kỷ ` followed by title-cased words (e.g., `Kỷ Hồng Bàng Thị`).
- **Edge Case**: Some chronological records start with Can Chi years that begin with "Kỷ" (e.g., `Kỷ Hợi, [39]`, `Kỷ Tỵ, năm thứ 2`).
- **Disambiguation**: An Era line will *not* contain a comma `,` or bracket `[` immediately after the Can Chi name. If it matches `^Kỷ (Hợi|Tỵ|Sửu|Mùi|Mão|Dậu)[,\[]`, it is a Record, not an Era.

### ReignMarker
- **Detection**: Short lines (< 50 characters) that are mostly Title Cased (excluding numbers/footnote markers) with no trailing punctuation like periods or commas.
- **Example**: `Kinh Dương Vương`, `Lạc Long Quân`.
- **Edge Cases**: If a `Record` appears in an `Era` before any `ReignMarker` (e.g., in `Kỷ Thuộc Tây Hán`), create an orphan/placeholder `ReignMarker` (e.g., `ReignMarker("Unknown/Placeholder")`) and append the Record to it.

### Record
- **Detection**: Any body text line that does not match Part, Volume, Era, or ReignMarker. This includes chronological entries like `Nhâm Tuất, năm thứ 17.` and original page markers like `[1a]`.
- **Example**: `[1b] Tên húy là Lộc Tục, con cháu họ Thần Nông6.`

### NoteReference
- **Detection in text**: A word immediately followed by one or more digits without a space.
- **Example**: `Hy thị1`, `Thần Nông6`.

## 4. Footnote Extraction Strategy

1. **Detecting Note Definitions**: At the bottom of a page, footnotes follow a strict pattern: a line with just a number (`^\d+$`), followed by an empty line, followed by the note text (which may span multiple lines until the next number or end of page).
2. **Detecting Note Markers**: In the page's body text, search for digits matching the extracted footnote numbers, typically attached to the end of a word (e.g., `châu3`).
3. **Association**:
   - When a note definition (e.g., `1`) is parsed at the bottom of page `N`.
   - Find `1` in the parsed Blocks of page `N`.
   - Calculate `pos` as the string index of the marker within the `Block.text`.
   - Create `NoteReference(part_idx, vol_idx, era_idx, block_idx, pos, note_text)`.
4. **Edge Cases/Fallback**:
   - **Missing Markers**: OCR errors often cause footnote markers to be missing from the body text. If a note definition `X` is extracted for a page, but the marker `X` is not found in the body text of that page, append the note to the **last Block on that page**, setting `pos = len(last_block.text)`. This ensures no historical notes are lost.

## 5. Page Handling Strategy

- **Page Markers**: Pages are delimited by `\x0c` (form feed).
- **Page Information**: The original physical page numbers (e.g., `3`) and woodblock leaf markers (e.g., `[1a]`, `[12b]`) are present.
  - Form feed strings should be used strictly for chunking and limiting the scope of footnote searches.
  - Woodblock leaf markers (e.g., `[1a]`) belong to the text itself and must be preserved verbatim in the `Record` text, as per the strict instruction to preserve original text.
- **Boundaries**: A Footnote definition found on a page *only* applies to markers found on that exact same page. State variables (Part, Volume, Era) persist across page boundaries.

## 6. Implementation Breakdown

### Step 1: Page Preprocessor
- **Goal**: Read the raw text, split by `\x0c`, and yield clean `(body_lines, footnote_dict)` tuples for each page.
- **Files**: Create `src/dvsktt_parser/parser.py`.
- **Functions**: `split_pages(text)`, `parse_page_content(page_string)`.
- **Expected Output**: A list of parsed pages, where each page has a list of body strings and a dictionary mapping footnote numbers to text definitions.

### Step 2: Main State Machine
- **Goal**: Process body lines sequentially to build the hierarchical `Document`.
- **Functions**: `parse_document(pages)`.
- **Implementation**:
  - Initialize `Document`, state indices (part=-1, vol=-1, era=-1, block=-1), and active parent pointers.
  - Iterate `pages`. For each line in `page.body_lines`:
    - Check structural regex/heuristics in order: Part -> Volume -> Era -> ReignMarker.
    - If a match is found, instantiate the model, append to parent, update indices.
    - If none match, it's a `Record`. Append to the current `ReignMarker`. Create orphan ReignMarkers if necessary.

### Step 3: Footnote Linker
- **Goal**: Safely associate footnote definitions with their markers in the Blocks.
- **Functions**: `link_footnotes_for_page(...)`.
- **Implementation**:
  - For each `Block` generated during a page, search for the expected footnote digits.
  - Compute `pos`. Create `NoteReference` and add to `Document.notes`.
  - Execute fallback logic for unmatched footnotes at the end of the page.

### Step 4: JSON Serialization
- **Goal**: Export the populated `Document` object to JSON.
- **Files**: Create `src/dvsktt_parser/exporter.py` or update `__main__.py`.
- **Expected Output**: Write structured hierarchy to `./output/chinh-hoa-18.json`.

## 7. Validation Strategy

- **Hierarchy Correctness**: Verify the JSON structure has nested Arrays corresponding exactly to Part > Volume > Era > Block. Ensure no Records exist outside a ReignMarker.
- **Note Extraction Correctness**: Check that `Document.notes` has exactly the same number of items as footnote definitions at the bottom of the pages. Verify that `pos` values fall within the string length of the referenced `Block.text`.
- **JSON Output Correctness**: Load the output JSON to ensure valid formatting and inspect the first and last records of Volume I to confirm texts match the original.

## 8. Risks and Ambiguities

- **Text Conversion Artifacts**: The source text is converted from a selectable PDF, so traditional OCR artifacts are absent. However, minor typos or formatting irregularities may still exist.
  - *Safe Handling*: Use robust matching where possible, but strictly adhere to deterministic parsing. Do not attempt ML corrections. Let minor typos remain (preserve original text).
- **Multiline Records**: A single historical record may span multiple paragraphs.
  - *Safe Handling*: Treat every distinct paragraph (non-empty line) that doesn't match a header as a distinct `Record`. This keeps parsing simple and deterministic.
- **Missing Footnote Markers**:
  - *Safe Handling*: As defined in the strategy, append orphaned notes to the last block of the current page with a position at the very end of the text. Do not discard them.
- **Ambiguous Reign Markers vs. Short Records**:
  - *Safe Handling*: The Title Case check without trailing punctuation is robust for names. If a short record happens to be title-cased and is misclassified as a ReignMarker, the damage is isolated. Do not build overly complex NLP rules.

## 9. E2E Testing Strategy

To ensure basic structural correctness, implement a simple End-to-End test that validates the hierarchy counts of the parsed `Document`. Note: Block and NoteReference counts can be ignored for these tests.

**Test Assertions:**
1. **Parts Count**: `Document.parts` must contain exactly 2 parts (Ngoại Kỷ and Bản Kỷ/Bản Kỷ Thực Lục/Bản Kỷ Tục Biên).
2. **Volumes per Part**:
   - Part 1 (Ngoại Kỷ) must have exactly **5** Volumes (Quyển I to V).
   - Part 2 (Bản Kỷ) must have exactly **22** Volumes (Quyển I to XXII).
3. **Era Verification**: Assert that the parsed Eras across the document align with this extracted list from the source:
   - Kỷ Hồng Bàng Thị
   - Kỷ Nhà Thục
   - Kỷ Nhà Triệu
   - Kỷ Thuộc Tây Hán
   - Kỷ Trưng Nữ Vương
   - Kỷ Thuộc Đông Hán
   - Kỷ Sĩ Vương
   - Kỷ Thuộc Ngô, Tấn, Tống, Tề, Lương
   - Kỷ Nhà Tiền Lý
   - Kỷ Triệu Việt Vương
   - Kỷ Hậu Lý
   - Kỷ Thuộc Tùy Đường
   - Kỷ Nam Bắc Phân Tranh
   - Kỷ Nhà Ngô
   - Kỷ nhà Đinh
   - Kỷ NHÀ LÊ
   - Kỷ Nhà Lý
   - Kỷ Nhà Trần
   - Kỷ Hậu Trần
   - Kỷ Nhà Lê
   - Kỷ Hoàng Triều Nhà Lê

*Note: Ensure Era matching filters out chronological records that merely begin with a Can Chi "Kỷ" (e.g., "Kỷ Hợi").*
