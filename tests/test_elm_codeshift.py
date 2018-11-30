from elm_doc import elm_codeshift


def test_elm_codeshift_strips_ports_from_single_line_declaration():
    source = 'port cmd : String -> Cmd ()'
    actual = elm_codeshift.strip_ports_from_string(source)
    expected = '''cmd : String -> Cmd ()
cmd a0 = Cmd.none
'''
    assert actual == expected


def test_elm_codeshift_strips_ports_from_multiline_declaration():
    source = '''
-- all arguments on the next line
port cmd :
  String -> Cmd ()

{-| last argument on the next line
-}
port cmd : String
  -> Cmd ()

-- suddenly, an unrelated function
func : ()

{- first and last
   argument on the next line
-}
port sub :
  Sub ()

port sub1 : Sub ()

{-| with interspersed comments -}
port cmd : String
    -- Inline comment
  -> Foo
  {- Single line comment -}
  -> Foo
  {-| Single line doc comment -}
  -> Foo
  {-| Multi line
comment -}
  -> Cmd ()
'''
    actual = elm_codeshift.strip_ports_from_string(source)
    expected = '''
-- all arguments on the next line
cmd :
  String -> Cmd ()
cmd a0 = Cmd.none

{-| last argument on the next line
-}
cmd : String
  -> Cmd ()
cmd a0 = Cmd.none

-- suddenly, an unrelated function
func : ()

{- first and last
   argument on the next line
-}
sub :
  Sub ()
sub = Sub.none

sub1 : Sub ()
sub1 = Sub.none

{-| with interspersed comments -}
cmd : String
    -- Inline comment
  -> Foo
  {- Single line comment -}
  -> Foo
  {-| Single line doc comment -}
  -> Foo
  {-| Multi line
comment -}
  -> Cmd ()
cmd a0 a1 a2 a3 = Cmd.none
'''
    assert actual == expected
