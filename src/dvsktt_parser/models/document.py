from typing import List, Union

class Document:
    def __init__(self):
        self.parts: List['Part'] = []
        self.notes: List['NoteReference'] = []

    def add_part(self, part: 'Part'):
        self.parts.append(part)

    def add_note(self, note_reference: 'NoteReference'):
        self.notes.append(note_reference)
