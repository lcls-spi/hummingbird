import h5py
import numpy as np

class H5Reader:
    def __init__(self, filename, key=None):
        self._fileno = h5py.File(filename, 'r')
        if key is not None:
            self.dataset = self.load_dataset(key)
            self._fileno.close()
            
    def load_dataset(self, key):
        return self._fileno[key][:]
        
class MaskReader(H5Reader):
    def __init__(self, filename, key='data/data'):
        H5Reader.__init__(self, filename, key)
        self.integer_mask = self.dataset.astype(np.int)
        self.boolean_mask = self.dataset.astype(np.bool)

class GeometryReader(H5Reader):
    def __init__(self, filename):
        H5Reader.__init__(self, filename)
        self.x = np.floor(self._fileno['x'][:]).astype(np.int)
        self.y = np.floor(self._fileno['y'][:]).astype(np.int)
        self._fileno.close()

