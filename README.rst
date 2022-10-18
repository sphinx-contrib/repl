==========================================================================
sphinxcontrib-repl - Sphinx directives to auto-evaluate Python code-blocks
==========================================================================

The ``sphinxcontrib-repl`` directives automatically run their content line-by-line in 
Python REPL interpreter during Sphinx builds the host reStructuredText files. 
The code-blocks are then replaced by ``doctest`` blocks containing the input/output 
lines as appear in the interpreter.

--------
Contents
--------

- `Installation <Installation_>`_
- `Basic Usage <Basic Usage_>`_

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
       sphinxcontrib_repl,
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
to run in the background for each rST document until the document is fully parsed. With the 
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

Finally, to hide nuisance operations (e.g., importing common libraries), 
use ``repl-quiet`` block:

.. code-block:: rst

   .. repl-quiet::

      import numpy as np

After this block, the Numpy package is loaded by the interpreter, but the import
line will not be printed in the document.
