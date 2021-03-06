#!/usr/bin/env python
#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

import os, subprocess

for document in ( "README.txt", "Developer_Manual.rst", "Changelog.rst" ):
    assert 0 == subprocess.call(
        "rst2pdf %(document)s" % {
            "document" : document
        },
        shell = True
    )

if not os.path.exists( "man" ):
    os.mkdir( "man" )

assert 0 == subprocess.call( "help2man -n 'the Python compiler' --no-discard-stderr --no-info --include doc/nuitka-man-include.txt ./bin/nuitka >doc/nuitka.1", shell = True )
assert 0 == subprocess.call( "help2man -n 'the Python compiler' --no-discard-stderr --no-info ./bin/nuitka-python >doc/nuitka-python.1", shell = True )

for manpage in ( "doc/nuitka.1", "doc/nuitka-python.1" ):
    manpage_contents = open( manpage ).readlines()
    new_contents = []
    mark = False

    for count, line in enumerate( manpage_contents ):
        if mark:
            line = ".SS " + line + ".BR\n"
            mark = False
        elif line == ".IP\n" and manpage_contents[ count + 1 ].endswith( ":\n" ):
            mark = True
            continue

        if line == r"\fB\-\-g\fR++\-only" + "\n":
            line = r"\fB\-\-g\++\-only\fR" + "\n"

        new_contents.append( line )

    open( manpage, "w" ).writelines( new_contents )

assert 0 == subprocess.call( "man2html doc/nuitka.1 >doc/man-nuitka.html", shell = True )
assert 0 == subprocess.call( "man2html doc/nuitka-python.1 >doc/man-nuitka-python.html", shell = True )

def getFile( filename ):
    return open( filename ).read()

contents = getFile( "doc/man-nuitka.html" )
new_contents = contents[ : contents.rfind( "<HR>" ) ] + contents[ contents.rfind( "</BODY>" ) : ]
assert new_contents != contents
contents = new_contents
new_contents = contents[ : contents.rfind( '<A HREF="#index">Index</A>' ) ] + contents[ contents.rfind( '</A><HR>' ) : ]
assert new_contents != contents
open( "doc/man-nuitka.html", "w" ).write( new_contents )

contents = getFile( "doc/man-nuitka-python.html" )
new_contents = contents[ : contents.rfind( "<HR>" ) ] + contents[ contents.rfind( "</BODY>" ) : ]
assert new_contents != contents
contents = new_contents
new_contents = contents[ : contents.rfind( '<A HREF="#index">Index</A>' ) ] + contents[ contents.rfind( '</A><HR>' ) : ]
assert new_contents != contents


open( "doc/man-nuitka-python.html", "w" ).write( new_contents )
