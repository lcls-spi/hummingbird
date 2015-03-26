"""Provides a ring buffer for scalar and numpy data.
It's always possible to retrieve the buffer data as a numpy array in O(1)
This is achieve by always inserting two copies of any appended data, so
it's a bit slower to add data, and it takes twice as much memory as a
regular buffer.
"""

import numpy

class RingBuffer(object):
    """Provides a ring buffer for scalar and numpy data.
    It's always possible to retrieve the buffer data as a numpy array in O(1)
    This is achieve by always inserting two copies of any appended data, so
    it's a bit slower to add data, and it takes twice as much memory as a
    regular buffer.
    """
    def __init__(self, maxlen):
        self._index = 0
        self._len = 0
        self._maxlen = maxlen
        self._data = None
    def append(self, x):
        """Append a value to the end of the buffer"""
        if(self._data is None):
            self._init_data(x)
        try:
            self._data[self._index] = x
        except ValueError:
            self._init_data(x)
            self._index = 0
            self._len = 0
            self._data[self._index] = x

        self._data[self._index + self._maxlen] = x
        self._index = (self._index + 1) % self._maxlen
        if(self._len < self._maxlen):
            self._len += 1

    def _init_data(self, x):
        """Initialize the buffer with the given data"""
        try:
            self._data = numpy.empty(tuple([2*self._maxlen]+list(x.shape)),
                                     x.dtype)
        except AttributeError:
            self._data = numpy.empty([2*self._maxlen], type(x))

    def __array__(self):
        """Return a numpy array with the buffer data"""
        return self._data[self._maxlen+self._index-self._len:self._maxlen+self._index]

    def __len__(self):
        """Return the length of the buffer"""
        return self._len

    def clear(self):
        """Empty the buffer"""
        self._len = 0
        self._index = 0

    @property
    def shape(self):
        """Returns the shape of the buffer, like a numpy array"""
        if(len(self._data.shape) == 1):
            return (self._len,)
        else:
            return (self._len,)+self._data.shape[1:]


    def _convert_dim(self, args):
        """Convert getitem arguments into internal indexes"""
        if(isinstance(args, slice)):
            start = self._maxlen+self._index-self._len
            if(args.start is None):
                if(args.step is not None and args.step < 0):
                    start = self._maxlen+self._index-1
            elif(args.start > 0):
                start += args.start
            elif(args.start < 0):
                start += args.start + self._len

            stop = self._maxlen+self._index
            if(args.stop is None):
                if(args.step is not None and args.step < 0):
                    stop = self._maxlen+self._index-self._len-1
            elif(args.stop > 0):
                stop += args.stop-self._len
            elif(args.stop < 0):
                stop += args.stop
            return slice(start, stop, args.step)
        else:
            if args < 0:
                args = self._len + args
            return self._maxlen+self._index-self._len + args

    def __getitem__(self, args):
        """Returns items from the buffer, just like a numpy array"""
        if(isinstance(args, tuple)):
            args = list(args)
            args[0] = self._convert_dim(args[0])
            return self._data[tuple(args)]
        else:
            return self._data[self._convert_dim(args)]



