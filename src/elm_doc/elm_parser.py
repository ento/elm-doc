'''
note: this is by no means a complete Elm syntax parser.
'''
import enum
from parsy import generate, regex, string
import attr


class PortType(enum.Enum):
    Command = 'Cmd'
    Subscription = 'Sub'


@attr.s(auto_attribs=True)
class PortInfo:
    name: str
    args: [str]
    port_type: PortType


def lexeme(p):
    """
    From a parser (or string), make a parser that consumes
    whitespace on either side.
    """
    if isinstance(p, str):
        p = string(p)
    return regex(r'\s*') >> p << regex(r'\s*')


func_name = regex(r'[a-z][a-zA-Z0-9_]*').desc('function name')
simple_parens_argument = lexeme(regex(r'[^(){}]+')).desc('no parens expression')
closing_parens = {'(': ')', '{': '}'}


@generate
def nested_parens_argument():
    opening = yield lexeme(regex(r'[({]')).desc('opening brace')

    content = yield parens_argument.many()

    expected_closing = lexeme(closing_parens[opening]).desc('closing brace')
    closing = yield expected_closing

    return opening + ''.join(content) + closing


parens_argument = lexeme('()') | simple_parens_argument | nested_parens_argument
no_parens_argument = lexeme(regex(r'[^({][^-]+')).desc('arg without parens')
argument = lexeme('()') | no_parens_argument | nested_parens_argument


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
