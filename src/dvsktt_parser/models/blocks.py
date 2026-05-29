from typing import Union

class ReignMarker:
    def __init__(self, text: str):
        self.text = text

class Record:
    def __init__(self, text: str):
        self.text = text

Block = Union[ReignMarker, Record]
