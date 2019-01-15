import pytest
import parsy

from elm_doc import elm_parser
from elm_doc.elm_parser.ports import PortType


def test_is_port_module(module_fixture_path):
    testcases = [
        ('Main.elm', False),
        ('PublicFunctionNotInAtDocs.elm', False),
        ('PortModuleB.elm', True),
    ]
    for elm_file, expected in testcases:
        assert elm_parser.is_port_module(module_fixture_path / elm_file) == expected


def test_func_name():
    valid_func_names = [
        'a',
        'camelCase',
        'with_underscore',
        'with_0',
    ]

    for valid_func_name in valid_func_names:
        assert elm_parser.ports.func_name.parse(valid_func_name) == valid_func_name

    invalid_func_names = [
        '012',
        '_underscore_first',
        'CapitalCamelCase',
    ]

    for invalid_func_name in invalid_func_names:
        with pytest.raises(parsy.ParseError):
            assert elm_parser.ports.func_name.parse(invalid_func_name)


def test_parse_port_declaration():
    ports = [
        ('port cmd : Cmd a', 'cmd', PortType.Command, []),
        ('port sub : Sub a', 'sub', PortType.Subscription, []),
        ('port cmd : ()->Cmd a', 'cmd', PortType.Command, ['()']),
        ('port cmd : Module.Type -> Cmd a', 'cmd', PortType.Command, ['Module.Type']),
        ('port cmd : (String) -> Cmd a', 'cmd', PortType.Command, ['(String)']),
        ('port cmd : (String -> a) -> Cmd a', 'cmd', PortType.Command, ['(String -> a)']),
        ('port cmd : ({b: Int} -> a) -> Cmd a', 'cmd', PortType.Command, ['({b: Int}-> a)']),
        ('port cmd : {b: String} -> Cmd a', 'cmd', PortType.Command, ['{b: String}']),
        ('port cmd : {b: (a -> a)} -> Cmd a', 'cmd', PortType.Command, ['{b: (a -> a)}']),
        ('port cmd : {b: (a -> {c: a} -> Module.Type)} -> Cmd a',
         'cmd', PortType.Command, ['{b: (a -> {c: a}-> Module.Type)}']),
        ('port cmd : {b: (a -> {c: a} -> ())} -> Cmd a', 'cmd', PortType.Command, ['{b: (a -> {c: a}-> ())}']),
        ('port cmd : () -> () -> Cmd a', 'cmd', PortType.Command, ['()', '()']),
        ('port cmd : () -> () -> Cmd a', 'cmd', PortType.Command, ['()', '()']),

        # test cases from elm-syntax
        # https://github.com/stil4m/elm-syntax/blob/73b5afe9a5816e4ee4ba36168deefe4a119d7d2d/tests/tests/Elm/Parser/TypeAnnotationTests.elm
        ('port cmd : ( (), ()) -> Cmd a', 'cmd', PortType.Command, ['((), ())']),
        ('port cmd : ( () ) -> Cmd a', 'cmd', PortType.Command, ['(())']),
        ('port cmd : ( () , Maybe m ) -> Cmd a', 'cmd', PortType.Command, ['((), Maybe m )']),
        ('port cmd : Foo.Bar -> Cmd a', 'cmd', PortType.Command, ['Foo.Bar']),
        ('port cmd : (Foo.Bar) -> Cmd a', 'cmd', PortType.Command, ['(Foo.Bar)']),
        ('port cmd : Foo () a Bar -> Cmd a', 'cmd', PortType.Command, ['Foo () a Bar']),
        ('port cmd : (Foo () a Bar) -> Cmd a', 'cmd', PortType.Command, ['(Foo ()a Bar)']),
        ('port cmd : {} -> Cmd a', 'cmd', PortType.Command, ['{}']),
        ('port cmd : ({}) -> Cmd a', 'cmd', PortType.Command, ['({})']),
        ('port cmd : {color: String } -> Cmd a', 'cmd', PortType.Command, ['{color: String }']),
        ('port cmd : ({color: String }) -> Cmd a', 'cmd', PortType.Command, ['({color: String })']),
        ('port cmd : { attr | position : Vec2, texture : Vec2 } -> Cmd a',
         'cmd', PortType.Command, ['{attr | position : Vec2, texture : Vec2 }']),
        ('port cmd : ({ attr | position : Vec2, texture : Vec2 }) -> Cmd a',
         'cmd', PortType.Command, ['({attr | position : Vec2, texture : Vec2 })']),
        ('port cmd : {color: {r : Int, g :Int, b: Int } } -> Cmd a',
         'cmd', PortType.Command, ['{color: {r : Int, g :Int, b: Int }}']),
        ('port cmd : ({color: {r : Int, g :Int, b: Int } }) -> Cmd a',
         'cmd', PortType.Command, ['({color: {r : Int, g :Int, b: Int }})']),
        ('port cmd : Foo -> Bar -> baz -> Cmd a', 'cmd', PortType.Command, ['Foo', 'Bar', 'baz']),
        ('port cmd : cMsg -> cModel -> a -> Cmd a', 'cmd', PortType.Command, ['cMsg', 'cModel', 'a']),
        ('port cmd : ( cMsg -> cModel -> a ) -> b -> Cmd a',
         'cmd', PortType.Command, ['(cMsg -> cModel -> a )', 'b']),
        ('port cmd : List(String) -> Cmd a', 'cmd', PortType.Command, ['List(String)']),
        ('port cmd : (List(String)) -> Cmd a', 'cmd', PortType.Command, ['(List(String))']),
    ]
    for src, name, port_type, args in ports:
        info = elm_parser.parse_port_declaration(src)
        assert info.name == name
        assert info.port_type == port_type
        assert info.args == args
