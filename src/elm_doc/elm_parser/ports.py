'''
Functions for parsing a port declaration.
'''
import enum

from parsy import generate, regex, string
import attr


class PortType(enum.Enum):
    Command = 'Cmd'
    Subscription = 'Sub'


@attr.s
class PortInfo:
    name = attr.ib()  # str
    args = attr.ib()  # [str]
    port_type = attr.ib()  # PortType


def lexeme(p):
    """
    From a parser (or string), make a parser that consumes
    whitespace on either side.
    """
    if isinstance(p, str):
        p = string(p)
    return regex(r'\s*') >> p << regex(r'\s*')


func_name = regex(r'[a-z][a-zA-Z0-9_]*').desc('function name')
no_parens_argument = lexeme(regex(r'[^({][^-]+')).desc('arg without outer parens')


@generate
def parens_argument():
    opening = yield lexeme(regex(r'[({]')).desc('opening brace')

    content = yield parens_content.many()

    parens_pairs = {'(': ')', '{': '}'}
    expected_closing = lexeme(parens_pairs[opening]).desc('closing brace')
    closing = yield expected_closing

    return opening + ''.join(content) + closing


string_without_parens = lexeme(regex(r'[^(){}]+')).desc('string w/o parens')
parens_content = lexeme('()') | string_without_parens | parens_argument
argument = lexeme('()') | no_parens_argument | parens_argument


@generate
def port_info():
    '''Parse port declaration. This parser only concerns itself with information
    necessary for producing a dummy implementation of the function in order to
    make the elm compiler happy when generating documentation for a project disguised
    as a package. Ports are not allowed in packages, so we need to transform them
    into ordinary functions.
    '''
    yield lexeme('port')
    port_name = yield lexeme(func_name)
    yield lexeme(':')
    port_args = yield (argument << lexeme('->')).many()
    port_value = yield lexeme('Cmd') | lexeme('Sub')
    port_type = PortType(port_value)
    yield regex(r'\S+').desc('remainder')
    return PortInfo(
        name=port_name,
        args=[arg.strip() for arg in port_args],
        port_type=port_type)


parse_port_declaration = port_info.parse
