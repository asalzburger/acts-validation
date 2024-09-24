""" Some algebraic utilities. """
import numpy as np

def distance( x0 : float, y0 : float, z0 : float,
              x1 : float, y1 : float, z1 : float ) -> float:
        """ Calculate the difference between two vectors. """
        return ((x0 - x1)**2 + (y0 - y1)**2 + (z0 - z1)**2)**0.5

# The vectorized version of the function
np_distance = np.vectorize(distance)
