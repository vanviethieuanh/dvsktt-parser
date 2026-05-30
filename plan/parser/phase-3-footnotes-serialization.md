# Phase 3: Footnote Linker & Serialization

## Project Context & Data Structure
We are building a parser for "Đại Việt Sử Ký Toàn Thư" that converts text into structured JSON.

The hierarchical models are:
- **Document**: The root container holding a list of `Part` objects and a global list of `NoteReference` objects.
- **Part** -> **Volume** -> **Era** -> **Block** (ReignMarker/Record).
- **NoteReference**: A globally stored pointer that links a footnote definition (extracted in Phase 1) to a specific location in a `Block` (extracted in Phase 2). It uses indices (`part`, `volume`, `era`, `block`) to resolve the exact block, and `pos` (character index) to pinpoint the marker.

## Goal: Footnote Linker & JSON Serialization
Safely associate footnote definitions with their markers in the Blocks, and export the resulting `Document` object to JSON.

## Footnote Linker Strategy
1. **Detecting Note Markers**: In the page's body text (Blocks), search for digits matching the extracted footnote numbers, typically attached to the end of a word (e.g., `châu3`). Note markers like `Hy thị1` appear as a word immediately followed by one or more digits without a space.
2. **Association**:
   - For each note definition (e.g., `1`) parsed at the bottom of page `N`.
   - Find the marker `1` in the parsed Blocks of page `N`.
   - Calculate `pos` as the string index of the marker within the `Block.text`.
   - Create `NoteReference(part_idx, vol_idx, era_idx, block_idx, pos, note_text)` and append to `Document.notes`.
3. **Edge Cases/Fallback**:
   - **Missing Markers**: Text conversion irregularities may cause footnote markers to be missing. If a note definition `X` is extracted for a page, but the marker `X` is not found in the body text of that page, append the note to the **last Block on that page**, setting `pos = len(last_block.text)`. Do not discard notes.
   - **Page Boundaries**: A Footnote definition found on a page *only* applies to markers found on that exact same physical page.

## Serialization Strategy
- **Goal**: Export the populated `Document` object to JSON.
- **Files**: Create `src/dvsktt_parser/exporter.py` or update `__main__.py`.
- **Expected Output**: Write the fully structured hierarchy (including globally stored notes) to `./output/chinh-hoa-18.json`.