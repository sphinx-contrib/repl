Testing tabular images

.. repl::
   :table-ncols: 2
   :mpl-bbox: tight
   :mpl-pad-inches: 0.01

   from matplotlib import pyplot as plt
   import numpy as np

   plt.figure()   
   plt.plot(np.random.randn(100))
   plt.title('plot 1')
   plt.figure()   
   plt.plot(np.random.randn(100))
   plt.title('plot 2')
   plt.figure()   
   plt.plot(np.random.randn(100))
   plt.title('plot 3')
   # plt.figure()   
   # plt.plot(np.random.randn(100))
   # plt.title('plot 4')
   plt.show()

======== ====
 bread   £2
 butter  £30
======== ====