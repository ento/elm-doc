import pytest
import parsy

from elm_doc import elm_parser
from elm_doc.elm_parser import PortType


def test_func_name():
    valid_func_names = [
        'a',
        'camelCase',
        'with_underscore',
        'with_0',
    ]

    for valid_func_name in valid_func_names:
        assert elm_parser.func_name.parse(valid_func_name) == valid_func_name

    valid_func_names = [
        '012',
        '_underscore_first',
        'CapitalCamelCase',
    ]

    for invalid_func_name in valid_func_names:
        with pytest.raises(parsy.ParseError):
            assert elm_parser.func_name.parse(invalid_func_name)


def test_port_info():
    ports = [
        ('port cmd : Cmd a', 'cmd', PortType.Command, []),
        ('port sub : Sub a', 'sub', PortType.Subscription, []),
        ('port cmd : () -> Cmd a', 'cmd', PortType.Command, ['()']),
        ('port cmd : Module.Type -> Cmd a', 'cmd', PortType.Command, ['Module.Type']),
        ('port cmd : (String) -> Cmd a', 'cmd', PortType.Command, ['(String)']),
        ('port cmd : (String -> a) -> Cmd a', 'cmd', PortType.Command, ['(String -> a)']),
        ('port cmd : ({b: Int} -> a) -> Cmd a', 'cmd', PortType.Command, ['({b: Int}-> a)']),
        ('port cmd : {b: String} -> Cmd a', 'cmd', PortType.Command, ['{b: String}']),
        ('port cmd : {b: (a -> a)} -> Cmd a', 'cmd', PortType.Command, ['{b: (a -> a)}']),
        ('port cmd : {b: (a -> {c: a} -> Module.Type)} -> Cmd a', 'cmd', PortType.Command, ['{b: (a -> {c: a}-> Module.Type)}']),
        ('port cmd : {b: (a -> {c: a} -> ())} -> Cmd a', 'cmd', PortType.Command, ['{b: (a -> {c: a}-> ())}']),
        ('port cmd : () -> () -> Cmd a', 'cmd', PortType.Command, ['()', '()']),
    ]
    for src, name, port_type, args in ports:
        info = elm_parser.port_info.parse(src)
        assert info.name == name
        assert info.port_type == port_type
        assert info.args == args
