# -*- coding: utf-8 -*-
"""
    urlresolver XBMC Addon
    Copyright (C) 2013 Bstrdsmkr
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    Adapted for use in xbmc from:
    https://github.com/einars/js-beautify/blob/master/python/jsbeautifier/unpackers/packer.py
    
    usage:
    if detect(some_string):
        unpacked = unpack(some_string)

    Unpacker for Dean Edward's p.a.c.k.e.r, a part of javascript beautifier
    by Einar Lielmanis <einar@beautifier.io>

    written by Stefano Sanfilippo <a.little.coder@gmail.com>

Unpacker for Dean Edward's p.a.c.k.e.r
"""

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re

beginstr = ''
endstr = ''


def detect(source):
    """Detects whether `source` is P.A.C.K.E.R. coded."""
    global beginstr
    global endstr

    begin_offset = -1

    if PY3 and isinstance(source, bytes):
        source = "".join(chr(x) for x in source)

    mystr = re.search(
        "eval[ ]*\([ ]*function[ ]*\([ ]*p[ ]*,[ ]*a[ ]*,[ ]*c["
        " ]*,[ ]*k[ ]*,[ ]*e[ ]*,[ ]*",
        source,
    )

    if mystr:
        begin_offset = mystr.start()
        beginstr = source[:begin_offset]

    if begin_offset != -1:
        """ Find endstr"""
        source_end = source[begin_offset:]
        if source_end.split("')))", 1)[0] == source_end:
            try:
                endstr = source_end.split("}))", 1)[1]
            except IndexError:
                endstr = ""
        else:
            endstr = source_end.split("')))", 1)[1]

    return mystr is not None


def unpack(source):
    """Unpacks P.A.C.K.E.R. packed js code."""
    if PY3 and isinstance(source, bytes):
        source = "".join(chr(x) for x in source)

    payload, symtab, radix, count = _filterargs(source)

    if count != len(symtab):
        raise UnpackingError('Malformed p.a.c.k.e.r. symtab.')

    try:
        unbase = Unbaser(radix)
    except TypeError:
        raise UnpackingError('Unknown p.a.c.k.e.r. encoding.')
    
    def lookup(match):
        """Look up symbols in the synthetic symtab."""
        word = match.group(0)
        return symtab[unbase(word)] or word
    
    if not PY3:
        source = re.sub(r"\b\w+\b", lookup, payload)
    else:
        source = re.sub(r"\b\w+\b", lookup, payload, flags=re.ASCII)

    return _replacestrings(source)


def _filterargs(source):
    """Juice from a source file the four args needed by decoder."""
    if PY3 and isinstance(source, bytes):
        source = "".join(chr(x) for x in source)

    juicers = [
        (r"}\('(.*)', *(\d+|\[\]), *(\d+), *'(.*)'\.split\('\|'\), *(\d+), *(.*)\)\)"),
        (r"}\('(.*)', *(\d+|\[\]), *(\d+), *'(.*)'\.split\('\|'\)"),
    ]

    for juicer in juicers:
        args = re.search(juicer, source, re.DOTALL)
        if args:
            a = args.groups()
            if a[1] == "[]":
                a = list(a)
                a[1] = 62
                a = tuple(a)

            try:
                return a[0], a[3].split('|'), int(a[1]), int(a[2])
            except ValueError:
                raise UnpackingError('Corrupted p.a.c.k.e.r. data.')

    # could not find a satisfying regex
    raise UnpackingError('Could not make sense of p.a.c.k.e.r data (unexpected code structure)')


def _replacestrings(source):
    """Strip string lookup table (list) and replace values in source."""
    global beginstr
    global endstr

    if PY3 and isinstance(source, bytes):
        source = "".join(chr(x) for x in source)

    match = re.search(r'var *(_\w+)\=\["(.*?)"\];', source, re.DOTALL)

    if match:
        varname, strings = match.groups()
        startpoint = len(match.group(0))
        lookup = strings.split('","')
        variable = '%s[%%d]' % varname

        for index, value in enumerate(lookup):
            source = source.replace(variable % index, '"%s"' % value)

        return source[startpoint:]

    try:
        if beginstr:
            pass
    except:
        beginstr = ''
        endstr = ''

    return beginstr + source + endstr


class Unbaser(object):
    """Functor for a given base. Will efficiently convert
    strings to natural numbers."""

    ALPHABET = {
        62: "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        95: (
            " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        ),
    }

    def __init__(self, base):
        self.base = base

        # fill elements 37...61, if necessary
        if 36 < base < 62:
            if not hasattr(self.ALPHABET, self.ALPHABET[62][:base]):
                self.ALPHABET[base] = self.ALPHABET[62][:base]

        # If base can be handled by int() builtin, let it do it for us
        if 2 <= base <= 36:
            self.unbase = lambda string: int(string, base)
        else:
            # Build conversion dictionary cache
            try:
                self.dictionary = dict((cipher, index) for index, cipher in enumerate(self.ALPHABET[base]))
            except KeyError:
                raise TypeError('Unsupported base encoding.')

            self.unbase = self._dictunbaser
    
    def __call__(self, string):
        return self.unbase(string)
    
    def _dictunbaser(self, string):
        """Decodes a  value to an integer."""
        ret = 0

        for index, cipher in enumerate(string[::-1]):
            ret += (self.base ** index) * self.dictionary[cipher]

        return ret


class UnpackingError(Exception):
    """Badly packed source or general error. Argument is a
    meaningful description."""
    pass