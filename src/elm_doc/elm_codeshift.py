import logging
from pathlib import Path

import parsy

from elm_doc import elm_parser


logger = logging.getLogger(__name__)


def strip_ports(elm_file: Path) -> None:
    with elm_file.open() as f:
        source = f.read()

    output = []
    for i, line in enumerate(source.splitlines()):
        if line.startswith('port module'):
            output.append(line[len('port '):])
        elif line.startswith('port '):
            output.append(line[len('port '):])
            try:
                port_info = elm_parser.port_info.parse(line)
                output.append(_make_dummy_port_implementation(port_info))
            except parsy.ParseError:
                logger.info(('{}:{}: failed to parse a port declaration; ignoring. '
                             'this may be because this is inside a comment').format(str(elm_file), i))
        else:
            output.append(line)

    with elm_file.open('w') as f:
        f.write('\n'.join(output))


def _make_dummy_port_implementation(port_info: elm_parser.PortInfo) -> str:
    parts = [port_info.name]

    # arguments
    for i, _ in enumerate(port_info.args):
        parts.append('a{}'.format(i))

    parts.append('=')
    parts.append('{}.none'.format(port_info.port_type.value))
    return ' '.join(parts)
