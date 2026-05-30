import re
from typing import Dict, List, Optional, Tuple, Union

from .models.blocks import Block, Record, ReignMarker
from .models.document import Document
from .models.notes import NoteReference
from .models.structure import Era, Part, Volume


def split_pages(text: str) -> List[str]:
    """Splits raw text by form feed character into pages."""
    return text.split("\x0c")


def clean_page_lines(
    lines: List[str],
) -> Tuple[List[str], Optional[str], Optional[str]]:
    """Removes page numbers and headers from the top of the page."""
    first_non_empty_idx = -1
    for idx, l in enumerate(lines):
        if l.strip():
            first_non_empty_idx = idx
            break

    if first_non_empty_idx == -1:
        return lines, None, None

    page_num = None
    page_header = None
    skip_indices = set()

    # Check if the first non-empty line is a page number
    if lines[first_non_empty_idx].strip().isdigit():
        page_num = lines[first_non_empty_idx].strip()
        skip_indices.add(first_non_empty_idx)

        # Find next non-empty line
        next_non_empty_idx = -1
        for idx in range(first_non_empty_idx + 1, len(lines)):
            if lines[idx].strip():
                next_non_empty_idx = idx
                break

        if next_non_empty_idx != -1:
            l = lines[next_non_empty_idx].strip()
            if "-" in l and any(
                kw in l for kw in ["Đại Việt", "Sử Ký", "Toàn Thư", "Thực Lục", "Tựa"]
            ):
                page_header = l
                skip_indices.add(next_non_empty_idx)
    else:
        # Check if first non-empty line is a header
        l = lines[first_non_empty_idx].strip()
        if "-" in l and any(
            kw in l for kw in ["Đại Việt", "Sử Ký", "Toàn Thư", "Thực Lục", "Tựa"]
        ):
            page_header = l
            skip_indices.add(first_non_empty_idx)

    cleaned_lines = [l for idx, l in enumerate(lines) if idx not in skip_indices]
    return cleaned_lines, page_num, page_header


def get_footnote_split(lines: List[str]) -> int:
    """Finds the index where the footnote section starts on a page."""
    pot = []
    for idx, l in enumerate(lines):
        s_l = l.strip()
        if s_l.isdigit():
            val = int(s_l)
            if 1 <= val <= 50:
                if idx == len(lines) - 1 or lines[idx + 1].strip() == "":
                    pot.append((idx, val))

    if not pot:
        return len(lines)

    for i in range(len(pot)):
        suffix = pot[i:]
        nums = [p[1] for p in suffix]

        is_valid = False
        if len(nums) == 1:
            is_valid = True
        elif len(nums) > 1:
            if nums[0] == 1:
                is_increasing = True
                for k in range(1, len(nums)):
                    if nums[k] <= nums[k - 1] and nums[k] != 1:
                        is_increasing = False
                        break
                if is_increasing:
                    is_valid = True
            elif nums[1] == 1:
                is_increasing = True
                for k in range(2, len(nums)):
                    if nums[k] <= nums[k - 1] and nums[k] != 1:
                        is_increasing = False
                        break
                if is_increasing:
                    is_valid = True

        if is_valid:
            split_line_idx = suffix[0][0]
            if split_line_idx >= len(lines) * 0.2:
                return split_line_idx

    return len(lines)


def extract_footnotes(fn_lines: List[str]) -> Dict[int, str]:
    """Extracts a footnote mapping of number -> text."""
    nums = []
    paragraphs = []
    curr_para = []

    for line in fn_lines:
        s_line = line.strip()
        if s_line.isdigit():
            nums.append(int(s_line))
            if curr_para:
                paragraphs.append(" ".join(curr_para).strip())
                curr_para = []
        else:
            if s_line:
                curr_para.append(s_line)
            else:
                if curr_para:
                    paragraphs.append(" ".join(curr_para).strip())
                    curr_para = []
    if curr_para:
        paragraphs.append(" ".join(curr_para).strip())

    footnote_dict = {}
    if len(nums) == len(paragraphs) and len(nums) > 0:
        for num, text in zip(nums, paragraphs):
            footnote_dict[num] = text
    else:
        # Fallback to sequential mapping
        curr_num = None
        curr_text = []
        for line in fn_lines:
            s_line = line.strip()
            if s_line.isdigit():
                if curr_num is not None:
                    footnote_dict[curr_num] = " ".join(curr_text).strip()
                curr_num = int(s_line)
                curr_text = []
            else:
                if s_line:
                    curr_text.append(s_line)
        if curr_num is not None:
            footnote_dict[curr_num] = " ".join(curr_text).strip()

    return footnote_dict


def parse_page_content(page_string: str) -> Tuple[List[str], Dict[int, str]]:
    """Splits a single page into clean body lines and footnote definitions."""
    lines = page_string.splitlines()
    cleaned_lines, _, _ = clean_page_lines(lines)
    split_idx = get_footnote_split(cleaned_lines)

    body_lines = cleaned_lines[:split_idx]
    fn_lines = cleaned_lines[split_idx:]

    clean_body = [l.strip() for l in body_lines if l.strip()]
    footnote_dict = extract_footnotes(fn_lines)

    return clean_body, footnote_dict


def is_mostly_title_cased(text: str) -> bool:
    """Helper to check if a line is mostly Title Cased."""
    text = re.sub(r"\d+$", "", text).strip()
    text = text.replace("[", "").replace("]", "")
    words = [w for w in text.split() if w]
    if not words:
        return False
    cap_words = 0
    for w in words:
        if w[0].isupper() or w[0].isdigit() or not w[0].isalpha():
            cap_words += 1
    return (cap_words / len(words)) >= 0.7


def is_reign_marker(line: str) -> bool:
    """Detects if a line is a ReignMarker."""
    line = line.strip()
    if not line:
        return False
    if len(line) >= 50:
        return False
    cleaned = re.sub(r"\d+$", "", line).strip()
    if any(cleaned.endswith(p) for p in [".", ",", ";", ":", "?", "!", ")", "]"]):
        return False
    if re.match(r"^\[\d+[ab]\]$", cleaned):
        return False
    if "-" in line and (
        "Đại Việt" in line
        or "Sử Ký" in line
        or "Toàn Thư" in line
        or "Thực Lục" in line
    ):
        return False
    if line.startswith("Đại Việt Sử Ký") and any(
        line.endswith(s) for s in ["Toàn Thư", "Thực Lục", "Tục Biên"]
    ):
        return False
    if line.startswith("Quyển ") or line.startswith("Kỷ "):
        return False
    return is_mostly_title_cased(cleaned)


def find_last_block_in_doc(doc: Document) -> Optional[Tuple[int, int, int, int, Block]]:
    """Finds the last block created in the document."""
    if not doc.parts:
        return None
    last_part = doc.parts[-1]
    if not last_part.volumes:
        return None
    last_vol = last_part.volumes[-1]
    if not last_vol.eras:
        return None
    last_era = last_vol.eras[-1]
    if not last_era.blocks:
        return None
    last_block = last_era.blocks[-1]
    return (
        last_part.index,
        last_vol.index,
        last_era.index,
        len(last_era.blocks) - 1,
        last_block,
    )


def link_footnotes_for_page(
    doc: Document,
    page_blocks: List[Tuple[int, int, int, int, Block]],
    footnote_dict: Dict[int, str],
):
    """Links footnote definitions to specific positions within Blocks on a page."""
    for num, note_text in footnote_dict.items():
        found = False
        for p_idx, v_idx, e_idx, b_idx, block_obj in page_blocks:
            pattern = r"(?<=[^\d\W])" + str(num) + r"(?!\d)"
            match = re.search(pattern, block_obj.text)
            if match:
                pos = match.start()
                note_ref = NoteReference(
                    part=p_idx,
                    volume=v_idx,
                    era=e_idx,
                    block=b_idx,
                    pos=pos,
                    note=note_text,
                )
                doc.add_note(note_ref)
                found = True
                break

        if not found:
            if page_blocks:
                p_idx, v_idx, e_idx, b_idx, last_block_obj = page_blocks[-1]
                pos = len(last_block_obj.text)
                note_ref = NoteReference(
                    part=p_idx,
                    volume=v_idx,
                    era=e_idx,
                    block=b_idx,
                    pos=pos,
                    note=note_text,
                )
                doc.add_note(note_ref)
            else:
                last_info = find_last_block_in_doc(doc)
                if last_info:
                    p_idx, v_idx, e_idx, b_idx, last_block_obj = last_info
                    pos = len(last_block_obj.text)
                    note_ref = NoteReference(
                        part=p_idx,
                        volume=v_idx,
                        era=e_idx,
                        block=b_idx,
                        pos=pos,
                        note=note_text,
                    )
                    doc.add_note(note_ref)


def parse_document(pages_text: List[str]) -> Document:
    """Processes pages and runs the core state machine to build a hierarchical Document."""
    doc = Document()

    active_part = None
    active_vol = None
    active_era = None
    active_reign_marker = None

    part_idx = -1
    vol_idx = -1
    era_idx = -1
    block_idx = -1

    for i, page_string in enumerate(pages_text):
        body_lines, footnote_dict = parse_page_content(page_string)
        page_blocks = []

        for line in body_lines:
            # 1. Part check
            if (
                line.startswith("Đại Việt Sử Ký")
                and "-" not in line
                and any(
                    line.endswith(suffix)
                    for suffix in ["Toàn Thư", "Thực Lục", "Tục Biên"]
                )
                and ("Ngoại Kỷ" in line or "Bản Kỷ" in line)
            ):
                name = "Ngoại Kỷ" if "Ngoại Kỷ" in line else "Bản Kỷ"

                part = None
                for p in doc.parts:
                    if p.name == name:
                        part = p
                        break
                if part is None:
                    part_idx = len(doc.parts)
                    part = Part(index=part_idx, name=name)
                    doc.add_part(part)
                else:
                    part_idx = part.index

                active_part = part
                active_vol = None
                active_era = None
                active_reign_marker = None
                vol_idx = -1
                era_idx = -1
                block_idx = -1
                continue

            if active_part is None:
                # Skip front matter before the first Part header is encountered
                continue

            # 2. Volume check
            elif re.match(r"^Quyển\s+[IVXLCDM]+\d*$", line):
                if active_part is None:
                    part_idx = 0
                    active_part = Part(index=0, name="Ngoại Kỷ")
                    doc.add_part(active_part)

                vol_idx = len(active_part.volumes)
                active_vol = Volume(index=vol_idx, name=line)
                active_part.add_volume(active_vol)
                active_era = None
                active_reign_marker = None
                era_idx = -1
                block_idx = -1

            # 3. Era check
            elif (
                line.startswith("Kỷ ")
                and len(line) < 50
                and not (
                    re.match(r"^Kỷ\s+(Hợi|Tỵ|Sửu|Mùi|Mão|Dậu)([,\[]|$)", line)
                    or (
                        len(line.split()) >= 2
                        and ("," in line.split()[1] or "[" in line.split()[1])
                    )
                )
            ):
                if active_part is None:
                    part_idx = 0
                    active_part = Part(index=0, name="Ngoại Kỷ")
                    doc.add_part(active_part)
                if active_vol is None:
                    vol_idx = len(active_part.volumes)
                    active_vol = Volume(index=vol_idx, name="Quyển I")
                    active_part.add_volume(active_vol)

                clean_name = re.sub(r"\d+$", "", line).strip()
                if active_era is not None and active_era.name == clean_name:
                    pass
                else:
                    era_idx = len(active_vol.eras)
                    active_era = Era(index=era_idx, name=clean_name)
                    active_vol.add_era(active_era)
                    active_reign_marker = None
                    block_idx = -1

            # 4. ReignMarker check
            elif is_reign_marker(line):
                if active_part is None:
                    part_idx = 0
                    active_part = Part(index=0, name="Ngoại Kỷ")
                    doc.add_part(active_part)
                if active_vol is None:
                    vol_idx = len(active_part.volumes)
                    active_vol = Volume(index=vol_idx, name="Quyển I")
                    active_part.add_volume(active_vol)
                if active_era is None:
                    era_idx = len(active_vol.eras)
                    active_era = Era(index=era_idx, name="Unknown/Placeholder")
                    active_vol.add_era(active_era)
                    block_idx = -1

                block_idx = len(active_era.blocks)
                cleaned_rm_text = re.sub(r"\d+$", "", line).strip()
                active_reign_marker = ReignMarker(text=cleaned_rm_text)
                active_era.add_block(active_reign_marker)
                page_blocks.append(
                    (part_idx, vol_idx, era_idx, block_idx, active_reign_marker)
                )

            # 5. Record
            else:
                if active_part is None:
                    part_idx = 0
                    active_part = Part(index=0, name="Ngoại Kỷ")
                    doc.add_part(active_part)
                if active_vol is None:
                    vol_idx = len(active_part.volumes)
                    active_vol = Volume(index=vol_idx, name="Quyển I")
                    active_part.add_volume(active_vol)
                if active_era is None:
                    era_idx = len(active_vol.eras)
                    active_era = Era(index=era_idx, name="Unknown/Placeholder")
                    active_vol.add_era(active_era)
                    block_idx = -1
                if active_reign_marker is None:
                    block_idx = len(active_era.blocks)
                    active_reign_marker = ReignMarker(text="Unknown/Placeholder")
                    active_era.add_block(active_reign_marker)
                    page_blocks.append(
                        (part_idx, vol_idx, era_idx, block_idx, active_reign_marker)
                    )

                block_idx = len(active_era.blocks)
                record = Record(text=line)
                active_era.add_block(record)
                page_blocks.append((part_idx, vol_idx, era_idx, block_idx, record))

        # Link footnotes for the page
        if footnote_dict:
            link_footnotes_for_page(doc, page_blocks, footnote_dict)

    return doc
