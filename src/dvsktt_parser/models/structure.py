from typing import List

from .blocks import Block


class Part:
    def __init__(self, index: int, name: str = ""):
        self.index = index
        self.name = name
        self.volumes: List["Volume"] = []

    def add_volume(self, volume: "Volume"):
        self.volumes.append(volume)


class Volume:
    def __init__(self, index: int, name: str = ""):
        self.index = index
        self.name = name
        self.eras: List["Era"] = []

    def add_era(self, era: "Era"):
        self.eras.append(era)


class Era:
    def __init__(self, index: int, name: str = ""):
        self.index = index
        self.name = name
        self.blocks: List[Block] = []

    def add_block(self, block: Block):
        self.blocks.append(block)
