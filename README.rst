==========================================================================
sphinxcontrib-repl - Sphinx directives to auto-evaluate Python code-blocks
==========================================================================

The ``sphinxcontrib-repl`` directives automatically run their content line-by-line in 
Python REPL interpreter during during Sphinx builds the host reStructuredText files. 
The code-blocks are then replaced by ``doctest`` blocks containing the input/output 
lines as appear in the interpreter.

--------
Contents
--------

- `Installation <Installation_>`_
- `Basic usage <Basic Usage_>`_

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

To run Python expressions in the interpreter, list the lines in ``repl`` block:

.. code-block:: rst

   .. repl::
   
      2*3+4
      x=5
      f"{x=}"

This block will produce the following document block:

.. code-block:: python

   >>> 2*3+4
   10
   >>> x=5
   >>> f"{x=}"
   'x=5'

After the first ``repl`` block, a dedicated Python interpreter process will run 
in the background continuously for each rST document until the document is fully
parsed. Hence, the variables will carry between blocks. For example, after 
the above example, the variable ``x`` may be used in any ``repl`` blocks.

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
