# Phase 4: Validation & E2E Testing

## Project Context & Data Structure
We are building a parser for "Đại Việt Sử Ký Toàn Thư" that converts text into structured JSON. The models map from a root `Document` down to `Part`, `Volume`, `Era`, and `Block` levels.

## Goal: Validation and Testing
Implement a simple End-to-End test that validates the hierarchy counts and structural correctness of the parsed `Document`. Note: Block and NoteReference counts can be ignored for these tests.

## Test Assertions
1. **Parts Count**: `Document.parts` must contain exactly 2 parts (Ngoại Kỷ and Bản Kỷ/Bản Kỷ Thực Lục/Bản Kỷ Tục Biên).
2. **Volumes per Part**:
   - Part 1 (Ngoại Kỷ) must have exactly **5** Volumes (Quyển I to V).
   - Part 2 (Bản Kỷ) must have exactly **22** Volumes (Quyển I to XXII).
3. **Era Verification**: Assert that the parsed Eras across the document align exactly with this extracted list from the source:
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

*Note: Ensure the parser's Era matching logic correctly filters out chronological records that merely begin with a Can Chi "Kỷ" (e.g., "Kỷ Hợi"), so they don't incorrectly appear in this Era list.*

## Output Validation
- **Hierarchy Correctness**: Verify the JSON structure has nested Arrays corresponding exactly to Part > Volume > Era > Block. Ensure no Records exist outside a ReignMarker.
- **Note Extraction Correctness**: Check that `Document.notes` has exactly the same number of items as footnote definitions at the bottom of the pages. Verify that `pos` values fall within the string length of the referenced `Block.text`.
- **JSON Output**: Verify the `./output/chinh-hoa-18.json` is structurally valid and the first/last records of Volume I match the original text.