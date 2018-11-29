'''
Functions for parsing line-by-line.
'''
from typing import List, Iterator, Tuple, Type
import re
import enum

import attr


@attr.s
class RawSourceLine:
    '''A line of source code'''
    number = attr.ib()  # int
    type = attr.ib()  # RawLineType
    raw = attr.ib()  # str

    def as_chunk_line(self) -> 'ChunkLine':
        chunk_line_type = ChunkLineType.for_source_line(self)
        return ChunkLine(self.number, chunk_line_type, self.raw)

    def as_comment_line(self) -> 'ChunkLine':
        chunk_line_type = ChunkLineType.Comment
        return ChunkLine(self.number, chunk_line_type, self.raw)


class RawLineType(enum.Enum):
    PortModuleStart = re.compile(r'^port\s+module')
    PortFunctionStart = re.compile(r'^port\s+[a-z]')
    MultilineCommentInOne = re.compile(r'^\s*\{-.*-\}\s*$')
    MultilineCommentStart = re.compile(r'^\s*\{-')
    MultilineCommentEnd = re.compile(r'-\}\s*$')
    InlineComment = re.compile(r'^\s*--')
    TopLevelThing = re.compile(r'^\S')
    IndentedThing = re.compile(r'^\s+\S')
    EmptyLine = re.compile(r'^\s*$')


def _iter_source_lines(source: str) -> Iterator[RawSourceLine]:
    # The True argument keeps newlines as part of the split results
    for i, line in enumerate(source.splitlines(True)):
        for line_type in RawLineType:
            if line_type.value and line_type.value.search(line):
                yield RawSourceLine(i + 1, line_type, line)
                break
        else:
            raise Exception('Could not determine what kind of source line this is at line {}: {}'.format(
                i + 1, line))


@attr.s
class ChunkLine:
    '''A line of source code in a chunk'''
    number = attr.ib()  # int
    type = attr.ib()  # ChunkLineType
    raw = attr.ib()  # str

    def is_source(self) -> bool:
        return self.type == ChunkLineType.Source


class ChunkLineType(enum.Enum):
    Source = 1
    Comment = 2
    Empty = 3

    @classmethod
    def for_source_line(cls, source_line: RawSourceLine) -> 'ChunkLineType':
        if source_line.type in (RawLineType.PortModuleStart,
                                RawLineType.PortFunctionStart,
                                RawLineType.TopLevelThing,
                                RawLineType.IndentedThing):
            return cls.Source

        elif source_line.type in (RawLineType.MultilineCommentInOne,
                                  RawLineType.MultilineCommentStart,
                                  RawLineType.MultilineCommentEnd,
                                  RawLineType.InlineComment):
            return cls.Comment

        elif source_line.type in (RawLineType.EmptyLine,):
            return cls.Empty

        raise ValueError('Unknown RawLineType: {}. This is likely a bug'.format(source_line.type))


@attr.s
class Chunk:
    '''A semi-logical group of continuous SourceLines'''
    type = attr.ib()  # ChunkType
    lines = attr.ib()  # List[ChunkLine]

    def is_port_function(self) -> bool:
        return self.type == ChunkType.PortFunctionDeclaration

    def is_port_module(self) -> bool:
        return self.type == ChunkType.PortModuleDeclaration

    def raw_lines(self) -> List[str]:
        return [line.raw for line in self.lines]

    def non_comment_raw_lines(self) -> Iterator[str]:
        if self.type == ChunkType.MultilineComment:
            yield from ()
        for line in self.lines:
            if line.is_source():
                yield line.raw


class ChunkType(enum.Enum):
    PortModuleDeclaration = 1
    PortFunctionDeclaration = 2
    MultilineComment = 3
    Other = 4


@attr.s
class ChunkStore:
    '''Datastructure to hold Chunks during parsing'''
    current_chunk = attr.ib(default=None)  # Chunk
    ready_to_yield = attr.ib(default=None)  # Chunk

    def add(self, line: ChunkLine):
        '''Add a SourceLine to the currently active Chunk.'''
        if not self.current_chunk:
            self.current_chunk = Chunk(ChunkType.Other, [])
        self.current_chunk.lines.append(line)

    def add_and_pop(self, line: ChunkLine):
        '''Add a SourceLine to the currently active Chunk and mark as done.'''
        self.add(line)
        self.pop()

    def pop_and_add(self, chunk_type: ChunkType, line: ChunkLine):
        '''Mark the currently active Chunk as done and then
        start a new Chunk with the given type and starting line.'''
        self.pop()
        self.current_chunk = Chunk(chunk_type, [line])

    def pop(self):
        '''Mark the currently active Chunk as done.'''
        if self.current_chunk:
            self.ready_to_yield = self.current_chunk
            self.current_chunk = None

    def take(self):
        '''Move the chunk marked as done off of this store.'''
        chunk = self.ready_to_yield
        self.ready_to_yield = None
        return chunk


class ParsingState:
    '''What the parser is currently doing.'''


ParsingStateStack = List[Type[ParsingState]]


class NothingSpecial(ParsingState):
    @classmethod
    def on_source_line(cls,
                       line: RawSourceLine,
                       state_stack: ParsingStateStack,
                       store: ChunkStore) -> Tuple[ParsingStateStack, ChunkStore]:
        if line.type == RawLineType.PortModuleStart:
            # this line is the start of the next chunk, which is a port module declaration
            store.pop_and_add(ChunkType.PortModuleDeclaration, line.as_chunk_line())
            return ([DefiningPortModule], store)

        elif line.type == RawLineType.PortFunctionStart:
            # this line is the start of the next chunk, which is a port function
            store.pop_and_add(ChunkType.PortFunctionDeclaration, line.as_chunk_line())
            return ([DefiningPortFunction], store)

        elif line.type == RawLineType.MultilineCommentStart:
            # this line is the start of the next chunk, which is a multiline comment
            store.pop_and_add(ChunkType.MultilineComment, line.as_chunk_line())
            return ([DefiningMultilineComment], store)

        else:
            # this line is nothing special; add to the current chunk
            store.add(line.as_chunk_line())
            return (state_stack, store)


class DefiningPortModule(ParsingState):
    @classmethod
    def on_source_line(cls,
                       line: RawSourceLine,
                       state_stack: ParsingStateStack,
                       store: ChunkStore) -> Tuple[ParsingStateStack, ChunkStore]:
        if line.type == RawLineType.MultilineCommentStart:
            # this line is the start of a comment inside the port module declaration we're defining
            store.add(line.as_chunk_line())
            state_stack.append(DefiningMultilineComment)
            return (state_stack, store)

        elif line.type == RawLineType.PortFunctionStart:
            # this line is the start of the next chunk, which is a port function
            store.pop_and_add(ChunkType.PortFunctionDeclaration, line.as_chunk_line())
            return ([DefiningPortFunction], store)

        elif line.type == RawLineType.TopLevelThing:
            # this line is the start of the next chunk
            store.pop_and_add(ChunkType.Other, line.as_chunk_line())
            return ([NothingSpecial], store)

        else:
            # this line is part of the port module declaration we're defining.
            # note: this adds inline comments to the port declaration lines.
            store.add(line.as_chunk_line())
            return (state_stack, store)


class DefiningPortFunction(ParsingState):
    @classmethod
    def on_source_line(cls,
                       line: RawSourceLine,
                       state_stack: ParsingStateStack,
                       store: ChunkStore) -> Tuple[ParsingStateStack, ChunkStore]:
        if line.type == RawLineType.MultilineCommentStart:
            # this line is the start of a comment inside the port function we're defining
            store.add(line.as_chunk_line())
            state_stack.append(DefiningMultilineComment)
            return (state_stack, store)

        elif line.type == RawLineType.PortFunctionStart:
            # this line is the start of the next chunk, which is a port function
            store.pop_and_add(ChunkType.PortFunctionDeclaration, line.as_chunk_line())
            return ([DefiningPortFunction], store)

        elif line.type == RawLineType.TopLevelThing:
            # this line is the start of the next chunk
            store.pop_and_add(ChunkType.Other, line.as_chunk_line())
            state_stack = [NothingSpecial]
            return (state_stack, store)

        else:
            # this line is part of the port function we're defining.
            # note: this adds inline comments to the port declaration lines.
            store.add(line.as_chunk_line())
            return (state_stack, store)


class DefiningMultilineComment(ParsingState):
    @classmethod
    def on_source_line(cls,
                       line: RawSourceLine,
                       state_stack: ParsingStateStack,
                       store: ChunkStore) -> Tuple[ParsingStateStack, ChunkStore]:
        if line.type == RawLineType.MultilineCommentEnd:
            if len(state_stack) > 1:
                # we were defining a multiline comment inside of a port declaration.
                # add this line to the port declaration and pop the current state.
                store.add(line.as_chunk_line())
                state_stack = state_stack[:-1]
            else:
                # we were defining a top-level multiline comment.
                # add this very last line to that comment and mark it as done.
                store.add_and_pop(line.as_chunk_line())
                state_stack = [NothingSpecial]
            return (state_stack, store)

        else:
            store.add(line.as_comment_line())
            return (state_stack, store)


def iter_line_chunks(source: str) -> Iterator[Chunk]:
    state_stack = [NothingSpecial]
    store = ChunkStore()
    for line in _iter_source_lines(source):
        state_stack, store = state_stack[-1].on_source_line(line, state_stack, store)
        if store.ready_to_yield:
            yield store.take()
    if store.ready_to_yield:
        yield store.take()
    store.pop()
    if store.ready_to_yield:
        yield store.take()


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        source = f.read()
    for chunk in iter_line_chunks(source):
        for line in chunk.lines:
            raw = line[:-1] if line and line.raw[-1] == '\n' else line
            print(line.number, chunk.type.name, line.type.name, raw)
