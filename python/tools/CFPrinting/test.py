import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-3, 3, 256)
y = np.linspace(-3, 3, 256)
X, Y = np.meshgrid(x, y)
Z = X**2 + Y**2

plt.contour(X, Y, Z, (2, 4, 6, 8, 17))
plt.show()