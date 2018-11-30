'''
note: this is by no means a complete Elm syntax parser. In fact,
it can only do little more than splitting a port declaration
at meaningful boundaries.
'''
from pathlib import Path

from elm_doc.elm_parser.lines import ChunkType, Chunk, iter_line_chunks
from elm_doc.elm_parser.ports import PortInfo, parse_port_declaration

__all__ = [
    'ChunkType',
    'Chunk',
    'PortInfo',
    'is_port_module',
    'iter_line_chunks',
    'parse_port_declaration',
]


def is_port_module(path: Path) -> bool:
    with open(str(path)) as f:
        for line in f:
            if line.startswith('module '):
                return False
            elif line.startswith('port module '):
                return True
    return False
