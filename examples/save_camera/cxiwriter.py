import numpy
import h5py
import os
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

class CXIWriter:
    def __init__(self, filename, chunksize=2):
        self._filename = os.path.expandvars(filename)
        if os.path.exists(filename):
            logger.warning("File %s exists and is being overwritten" % filename)
        self._f = h5py.File(filename, "w")
        self._i = 0
        self._chunksize = chunksize

    def write(self, D):
        self._write_without_iterate(D)
        self._i += 1
        
    def _write_without_iterate(self, D, group_prefix="/"):
        for k in D.keys():
            if isinstance(D[k],dict):
                group_prefix_new = group_prefix + k + "/"
                log_debug(logger, "Writing group %s" % group_prefix_new)
                if k not in self._f[group_prefix]:
                    self._f.create_group(group_prefix_new)
                self._write_without_iterate(D[k], group_prefix_new)
            else:
                name = group_prefix + k
                logger.debug( "Writing dataset %s" % name)
                data = D[k]
                if k not in self._f[group_prefix]:
                    if numpy.isscalar(data):
                        maxshape = (None,)
                        shape = (self._chunksize,)
                        dtype = numpy.dtype(type(data))
                        if dtype == "S":
                            dtype = h5py.new_vlen(str)
                        axes = "experiment_identifier:value"
                    else:
                        data = numpy.asarray(data)
                        try:
                            h5py.h5t.py_create(data.dtype, logical=1)
                        except TypeError:
                            logger.warning("Could not save dataset %s. Conversion to numpy array failed" % name)
                            continue
                        maxshape = tuple([None]+list(data.shape))
                        shape = tuple([self._chunksize]+list(data.shape))
                        dtype = data.dtype
                        ndim = data.ndim
                        axes = "experiment_identifier"
                        if ndim == 1: axes = axes + ":x"
                        elif ndim == 2: axes = axes + ":y:x"
                        elif ndim == 3: axes = axes + ":z:y:x"
                    logger.debug("Create dataset %s [shape=%s, dtype=%s]" % (name,str(shape),str(dtype)))
                    self._f.create_dataset(name, shape, maxshape=maxshape, dtype=dtype)
                    self._f[name].attrs.modify("axes",[axes])
                if self._f[name].shape[0] <= self._i:
                    if numpy.isscalar(data):
                        data_shape = []
                    else:
                        data_shape = data.shape
                    new_shape = tuple([self._chunksize*(self._i/self._chunksize+1)]+list(data_shape))
                    logger.debug("Resize dataset %s [old shape: %s, new shape: %s]" % (name,str(self._f[name].shape),str(new_shape)))
                    self._f[name].resize(new_shape)
                logger.debug("Write to dataset %s at stack position %i" % (name, self._i))
                if numpy.isscalar(data):
                    self._f[name][self._i] = data
                else:
                    self._f[name][self._i,:] = data[:]

    def _shrink_stacks(self, group_prefix="/"):
        for k in self._f[group_prefix].keys():
            name = group_prefix + k
            if isinstance(self._f[name], h5py.Dataset):
                logger.debug("Shrinking dataset %s to stack length %i" % (name, self._i))
                s = list(self._f[name].shape)
                s.pop(0)
                s.insert(0, self._i)
                s = tuple(s)
                self._f[name].resize(s)
            else:
                self._shrink_stacks(name + "/")
                    
    def close(self):
        self._shrink_stacks()
        logger.debug("Closing file %s" % self._filename)
        self._f.close()
    
