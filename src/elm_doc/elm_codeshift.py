from typing import List
import logging
from pathlib import Path
import itertools

import parsy

from elm_doc import elm_parser
from elm_doc.elm_parser import Chunk


logger = logging.getLogger(__name__)


def strip_ports_from_file(elm_file: Path) -> None:
    source = elm_file.read_text()
    stripped = strip_ports_from_string(source, str(elm_file))
    elm_file.write_text(stripped)


def strip_ports_from_string(source: str, source_path: str = '<unknown>') -> str:
    output = []
    for chunk in elm_parser.iter_line_chunks(source):
        if chunk.is_port_function():
            output.extend(_rewrite_port_function(chunk, source_path))
        elif chunk.is_port_module():
            output.extend(_rewrite_port_module(chunk))
        else:
            output.extend(chunk.raw_lines())
    return ''.join(output)


def _rewrite_port_module(chunk: Chunk) -> List[str]:
    output = []
    for line in chunk.lines:
        if line.raw.startswith('port module'):
            output.append(line.raw[len('port '):])
        else:
            output.append(line.raw)
    return output


def _rewrite_port_function(chunk: Chunk, source_path: str) -> List[str]:
    output = []

    trailing_non_sources = list(reversed(list(itertools.takewhile(
        lambda l: not l.is_source(), reversed(chunk.lines)))))
    declaration_lines = chunk.lines[:-len(trailing_non_sources)] if trailing_non_sources else chunk.lines

    for line in declaration_lines:
        if line.raw.startswith('port '):
            output.append(line.raw[len('port '):])
        else:
            # These lines may contain comments which, semantically
            # speaking, belong to the next function: the output may
            # not make sense to human reader. Since our audience is
            # the Elm compiler, we don't care that much.
            output.append(line.raw)

    # If this chunk is the very last lines of a file, we may need to add a newline.
    if (not trailing_non_sources) and (not chunk.lines[-1].raw.endswith('\n')):
        output.append('\n')

    try:
        one_liner = ''.join([raw.strip() for raw in chunk.non_comment_raw_lines()])
        port_info = elm_parser.parse_port_declaration(one_liner)
        output.append(_make_dummy_port_implementation(port_info) + '\n')
    except parsy.ParseError:
        line_num = chunk.lines[0].number
        logger.error('''{}:{}: failed to parse a port declaration. We parsed it as:

  {}

If this is a valid port declaration, please submit a bug report'''.format(
            source_path, line_num, one_liner))
        raise

    for trailing_line in trailing_non_sources:
        output.append(trailing_line.raw)

    return output


def _make_dummy_port_implementation(port_info: elm_parser.PortInfo) -> str:
    parts = [port_info.name]

    # arguments
    for i, _ in enumerate(port_info.args):
        parts.append('a{}'.format(i))

    parts.append('=')
    parts.append('{}.none'.format(port_info.port_type.value))
    return ' '.join(parts)
