==========================================================================
sphinxcontrib-repl - Directives to auto-evaluate Python code-blocks
==========================================================================

``sphinxcontrib-repl`` is an extension to `Sphinx <https://www.sphinx-doc.org/>`_ 
document generator tool. The extension introduces ``repl`` and ``repl-quiet`` 
directives to run Python REPL interpreters during Sphinx builds the 
documentation. The content of the directives will be automatically evaluated 
line-by-line in the interpreter, and ``repl`` blocks will add what would be 
printed on the interpreter in the output document. 

--------
Contents
--------

- `Installation <Installation_>`_
- `Basic Usage <Basic Usage_>`_
- `Matplotlib Integration <Matplotlib Integration_>`_

------------
Installation
------------

Install from PyPI:

.. code-block::
   
   pip install sphinxcontrib-repl

Then, inside your Sphinx ``conf.py``, add ``sphinxcontrib_repl`` to your list of extensions 
(note: underscores not hyphens).


.. code-block:: Python

   extensions = [
       "sphinxcontrib_repl",
       # other extensions...
   ]

-----------
Basic Usage
-----------

To run Python code in the interpreter, list the code in a ``repl`` block:

.. code-block:: rst

   .. repl::
   
      2*3+4
      x=5
      f"{x=}"

First of such block will invoke a dedicated Python interpreter process, which will continue
to run in the background for each RST document until the document is fully parsed. With the 
interpreter, the above block of code will produce the following document block:

.. code-block:: python

   >>> 2*3+4
   10
   >>> x=5
   >>> f"{x=}"
   'x=5'

As the interpreter process will run continuously, the variables will carry between blocks. 
For example, after the above ``repl`` block, the variable ``x`` may be used in any 
subsequent ``repl`` blocks (unless you delete it):

.. code-block:: rst

   .. repl::
   
      x+4

will produce:

.. code-block:: python

   >>> x+4
   9

A REPL block may contain (potentially nested) condition/loop statements:

.. code-block:: rst

   .. repl::

      for i in range(5):
          if i>2:
              i+1

outputs

.. code-block:: python

   >>> for i in range(5):
   ...     if i>2:
   ...         i+1
   ...
   4
   5

Note that a trailing empty line to terminate the indented block will be inserted
automatically.

To hide nuisance operations (e.g., importing common libraries), 
use ``repl-quiet`` block:

.. code-block:: rst

   .. repl-quiet::

      import numpy as np

After this block, the Numpy package is loaded onto the interpreter, but the import
line will not be printed in the document.

--------------------------
Matplotlib Integration
--------------------------

Plotting ``matplotlib`` figures in the REPL interpreter process yields the figures
to be automatically exported to the document:

.. code-block:: rst
   
   .. repl::
      
      import numpy as np
      from matplotlib import pyplot as plt

      plt.plot(np.random.randn(100))
      plt.figure()
      plt.plot(np.random.randn(100))
      plt.show()

The above RST ``repl`` block generates the following Python code snippet and the 
figure images:

.. code-block:: python

   import numpy as np

   from matplotlib import pyplot as plt


   plt.plot(np.random.randn(100))
   [<matplotlib.lines.Line2D object at 0x0000025C046CCDF0>]

   plt.figure()
   <Figure size 800x400 with 0 Axes>

   plt.plot(np.random.randn(100))
   [<matplotlib.lines.Line2D object at 0x0000025C0471A7F0>]

   plt.show()

.. image:: docs/imgs/mpl_0_1.svg

.. image:: docs/imgs/mpl_0_2.svg

To hide the Python code, use the ``repl-quiet`` directive, which will only display 
the figures:

.. code-block:: rst

   .. repl-quiet::
      
      plt.plot(np.random.randn(100))
      plt.title('plotted in repl-quiet')
      plt.show()

This code prints only the image:

.. image:: docs/imgs/mpl_1_1.svg

--------------------------
Options
--------------------------

Visibility Control Options
^^^^^^^^^^^^^^^^^^^^^^^^^^

In ``repl`` directive content, input and output lines maybe hidden with boolean directive options:
``:hide-input: true`` and ``:hide-output: true`` hide input lines and output lines, respectively.

Also, their visibility could be toggled in the directive's Python command lines. Inserting the magic
comments listed below as a comment line will switch the visibility of input or output lines (or both).
In addition, using these magic comments inline with a Python command will set the visibility only for
the line.

=================  =====================  ===========
Directive          Magic comment          Description
=================  =====================  ===========
``:hide-input:``   ``#repl:hide-input``   Hide input
``:hide-output:``  ``#repl:hide-output``  Hide output
\                  ``#repl:show-input``   Show input
\                  ``#repl:show-output``  Show output 
\                  ``#repl:hide``         Hide both input and output
\                  ``#repl:show``         Show both input and output
=================  =====================  ===========

.. TODO
.. Matplotlib Options
.. ^^^^^^^^^^^^^^^^^^

.. ------------------------  ---------------  -----------
.. extension                 directive        description
.. ------------------------  ---------------  -----------
.. ``repl_mpl_disable``                       ``True`` to disable matplotlib support
.. ``repl_mpl_dpi``                                       
.. ``repl_mpl_format``
.. ``repl_mpl_figsize``      ``figsize``
.. ``repl_mpl_facecolor``    ``facecolor``
.. ``repl_mpl_edgecolor``    ``edgecolor``
.. ``repl_mpl_bbox``         ``bbox``
.. ``repl_mpl_pad_inches``   ``pad_inches``
.. ``repl_mpl_transparent``  ``transparent``
.. ``repl_mpl_rc_params``    ``rc-params``
.. ------------------------  ---------------  ----  ----  -----------
