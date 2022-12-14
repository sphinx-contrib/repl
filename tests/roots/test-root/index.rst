Run REPL during rst compiling

.. repl-quiet::

    import json
    'do not print this'
    y = 32

Create a repl block with auto-executing Python prompts, and it prints the commands as
`doctest`

.. repl::

   2*3+4
   x=5
   f"{x=}"

The same REPL shell is used throughout each RST document:

.. repl::

   x
   y


A REPL block may contain (potentially nested) condition/loop statements:

.. repl::

    for i in range(5):
        if i>2:
            i+1

Note that the indented code block does not need trailing empty line.

.. repl::
   :hide-output: true
   
   import numpy as np
   from matplotlib import pyplot as plt

   plt.plot(np.random.randn(100))
   plt.figure()
   plt.plot(np.random.randn(100))
   plt.show()

With ``repl-quiet`` directive, only the plotted figures are shown:

.. repl-quiet::
   :mpl-figsize: 6, 4
   :mpl-facecolor: orange
   :mpl-edgecolor: red
   :mpl-bbox: standard
   :mpl-pad-inches:  0.1
   :mpl-transparent:  False
   :mpl-rc-params:  {"lines.marker": "x", "lines.markersize": 3}
   :image-width: 50%
   
   plt.plot(np.random.randn(100))
   plt.title('plotted in repl-quiet')
   plt.show()

.. repl::

   #repl:hide-input
   'no input'
   'show input' #repl:show
   'no input again'
   #repl:show-input

   #repl:hide-output
   'no output'
   'show output' #repl:show
   'no output again'
   #repl:show-output
