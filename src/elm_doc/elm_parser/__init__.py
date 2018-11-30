'''
note: this is by no means a complete Elm syntax parser. In fact,
it can only do little more than splitting a port declaration
at meaningful boundaries.
'''
from elm_doc.elm_parser.lines import ChunkType, Chunk, iter_line_chunks
from elm_doc.elm_parser.ports import PortInfo, parse_port_declaration

__all__ = [
    'ChunkType',
    'Chunk',
    'PortInfo',
    'iter_line_chunks',
    'parse_port_declaration',
]
