Run REPL during rst compiling

.. repl-quiet ::

    import json
    'do not print this'
    y = 32

Create a repl block with auto-executing Python prompts, and it prints the commands as
`doctest`

.. repl ::

   2*3+4
   x=5
   f"{x=}"

The same REPL shell is used throughout each RST document:

.. repl ::

   x
   y


A REPL block may contain (potentially nested) condition/loop statements:

.. repl ::

    for i in range(5):
        if i>2:
            i+1

Note that the indented code block does not need trailing empty line.

