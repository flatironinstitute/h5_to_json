import numpy as np
import six
from .hdf5dtype import createDataType

if six.PY3:
    unicode = str

def get_value(X, data_dir=None, use_kachery=False, lazy=False):
    body = X

    ## note: this is duplicated code. will remedy in future ###########################
    datatype = body['type']
    if type(datatype) in (str, unicode) and datatype.startswith("datatypes/"):
        #committed datatype, just pass in the UUID part
        datatype = datatype[len("datatypes/"):]
    dims = ()  # if no space in body, default to scalar
    max_shape=None
    fill_value=None
    creation_props=None
    if 'creationProperties' in body:
        creation_props = body['creationProperties']
    if "shape" in body:
        shape = body["shape"]
        if shape["class"] == 'H5S_SIMPLE':
            dims = shape["dims"]
            if type(dims) == int:
                # convert int to array
                dim1 = shape
                dims = [dim1]
            if "maxdims" in shape:
                max_shape = shape["maxdims"]
                if type(max_shape) == int:
                    #convert to array
                    dim1 = max_shape
                    max_shape = [dim1]
                # convert H5S_UNLIMITED's to None's
                for i in range(len(max_shape)):
                    if max_shape[i] == 'H5S_UNLIMITED':
                        max_shape[i] = None
        elif shape["class"] == 'H5S_NULL':
            dims = None
    
    dt = createDataType(datatype)

    if "value" in body:
        value0 = body["value"]
        if dims is not None:
            return np.array(value0, dtype=dt).reshape(tuple(dims))
        else:
            return value0
    elif "valueHash" in body:
        if dims is None:
            raise Exception('This case not yet handled.')
        fname = None
        if data_dir:
            for alg in ['sha1', 'md5']:
                if alg in body['valueHash']:
                    fname = data_dir + '/{}_{}.dat'.format(alg, body['valueHash'][alg])
            if fname is None:
                raise Exception('Unexpected valueHash')
        elif use_kachery:
            try:
                import kachery as ka
            except:
                raise Exception('Kachery is not installed. Try "pip install --upgrade kachery".')

            for alg in ['sha1', 'md5']:
                if alg in body['valueHash']:
                    path0 = '{}://{}'.format(alg, body['valueHash'][alg])
            if path0 is None:
                raise Exception('Unexpected valueHash')
            if lazy:
                return LazyRemoteArray(path0, dtype=dt, shape=tuple(dims))
            fname = ka.load_file(path0)
            if fname is None:
                raise Exception('Unable to load file {}'.format(path0))
        else:
            raise Exception('Cannot retrieve data from valueHash because data_dir is not specified and use_kachery is False')
        
        return np.memmap(fname, dtype=dt, shape=tuple(dims))

class LazyRemoteArray:
    def __init__(self, path, dtype, shape):
        self._path = path
        self.dtype = dtype
        self.shape = shape
        self.ndim = len(self.shape)
    def __getitem__(self, index):
        import kachery as ka
        if isinstance(index, int):
            offset = index * self.dtype.itemsize
            with ka.open_file(self._path) as f:
                f.seek(offset)
                buf = f.read(self.dtype.itemsize)
                x = np.frombuffer(buf, dtype=self.dtype)
                return x[0]
        elif isinstance(index, slice):
            if self.ndim == 1:
                start = index.start
                stop = index.stop
                step = index.step
                if start is None:
                    start = 0
                if stop is None:
                    stop = self.shape[0]
                if step is None:
                    step = 1
                with ka.open_file(self._path) as f:
                    offset = start * self.dtype.itemsize
                    f.seek(offset)
                    buf = f.read(self.dtype.itemsize * (stop - start))
                    x = np.frombuffer(buf, dtype=self.dtype)
                    return x[::step]
            else:
                raise Exception('This slicing case not handled yet for LazyRemoteArray.')
        elif isinstance(index, tuple):
            if len(index) != 2:
                raise Exception('This slicing case not handled yet for LazyRemoteArray.')
            if self.ndim != len(index):
                raise Exception('This slicing case not handled yet for LazyRemoteArray.')
            index1 = index[0]
            start1 = index1.start
            stop1 = index1.stop
            step1 = index1.step
            if start1 is None:
                start1 = 0
            if stop1 is None:
                stop1 = self.shape[0]
            if step1 is None:
                step1 = 1
            index2 = index[1]
            start2 = index2.start
            stop2 = index2.stop
            step2 = index2.step
            if start2 is None:
                start2 = 0
            if stop2 is None:
                stop2 = self.shape[1]
            if step2 is None:
                step2 = 1
            b1 = len(range(start1, stop1, step1))
            b2 = len(range(start2, stop2, step2))
            shape0 = (b1, b2)
            with ka.open_file(self._path) as f:
                if step1 == 1:
                    f.seek(start1 * self.shape[1])
                    buf = f.read(self.dtype.itemsize * (stop1 - start1) * self.shape[1])
                    x = np.frombuffer(buf, dtype=self.dtype).reshape((stop1 - start1, self.shape[1]))
                    return x[:, start2:stop2:step2]
                elif step1 <= 10:
                    f.seek(start1 * self.shape[1])
                    buf = f.read(self.dtype.itemsize * (stop1 - start1) * self.shape[1])
                    x = np.frombuffer(buf, dtype=self.dtype).reshape((stop1 - start1, self.shape[1]))
                    return x[::step1, :][:, start2:stop2:step2]
                else:
                    ret = np.empty(shape=shape0, dtype=self.dtype)
                    for i1 in range(start1, stop1, step1):
                        offset = (i1 * self.shape[1] + start2) * self.dtype.itemsize
                        f.seek(offset)
                        buf = f.read(self.dtype.itemsize * (stop2 - start2))
                        x = np.frombuffer(buf, dtype=self.dtype)
                        ret[i1 - start1, :] = x[::step2]
                    return ret
        else:
            raise Exception('This slicing case not handled yet for LazyRemoteArray.')
        return None