import numpy as np
import six
from .hdf5dtype import createDataType

if six.PY3:
    unicode = str

def get_value(X, data_dir=None):
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
        if not data_dir:
            raise Exception('Cannot retrieve data from valueHash because data_dir is not specified')
        fname = None
        for alg in ['sha1', 'md5']:
            if alg in body['valueHash']:
                fname = data_dir + '/{}_{}.dat'.format(alg, body['valueHash'][alg])
        if fname is None:
            raise Exception('Unexpected valueHash')
        return np.memmap(fname, dtype=dt, shape=tuple(dims))
