import json

from .models.blocks import Block
from .models.document import Document
from .models.notes import NoteReference
from .models.structure import Era, Part, Volume


def block_to_dict(block: Block) -> dict:
    """Serializes a Block (ReignMarker/Record) to a dictionary."""
    return {"type": type(block).__name__, "text": block.text}


def era_to_dict(era: Era) -> dict:
    """Serializes an Era to a dictionary."""
    return {
        "index": era.index,
        "name": era.name,
        "blocks": [block_to_dict(b) for b in era.blocks],
    }


def volume_to_dict(volume: Volume) -> dict:
    """Serializes a Volume to a dictionary."""
    return {
        "index": volume.index,
        "name": volume.name,
        "eras": [era_to_dict(e) for e in volume.eras],
    }


def part_to_dict(part: Part) -> dict:
    """Serializes a Part to a dictionary."""
    return {
        "index": part.index,
        "name": part.name,
        "volumes": [volume_to_dict(v) for v in part.volumes],
    }


def note_reference_to_dict(note: NoteReference) -> dict:
    """Serializes a NoteReference to a dictionary."""
    return {
        "part": note.part,
        "volume": note.volume,
        "era": note.era,
        "block": note.block,
        "pos": note.pos,
        "note": note.note,
    }


def document_to_dict(doc: Document) -> dict:
    """Serializes a Document to a dictionary."""
    return {
        "parts": [part_to_dict(p) for p in doc.parts],
        "notes": [note_reference_to_dict(n) for n in doc.notes],
    }


def export_to_json(doc: Document, output_path: str):
    """Exports a Document object to a JSON file."""
    data = document_to_dict(doc)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
