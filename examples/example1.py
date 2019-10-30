#!/usr/bin/env python

import h5py
import numpy as np
import json
import h5_to_json as h5j

def main():
    # Create an example hdf5 file with a dataset
    create_sample_hdf5('test_example.h5')

    # Store in a Python dict, and data gets separately stored in a directory
    X = h5j.h5_to_dict('test_example.h5', data_dir='test_dir')

    # Write to a .json file
    with open('test_example.h5.json', 'w') as f:
        json.dump(X, f, indent=4)

    # Complete the round trip by writing a new hdf5 file
    h5j.dict_to_h5(X, 'test_example_roundtrip.h5', data_dir='test_dir')

    # Lets check to see if we've preserved the information
    X_roundtrip = h5j.h5_to_dict('test_example_roundtrip.h5', data_dir='test_dir')
    if json.dumps(X, sort_keys=True) == json.dumps(X_roundtrip, sort_keys=True):
        print('Roundtrip matches')
    else:
        print('WARNING: roundtrip does not match')
    
    # Convert to a hierarchical representation for convenience
    Y = h5j.hierarchy(X)

    # Retrieve the dataset array (values come from the data directory)
    ds1 = h5j.get_value(Y['root']['group1']['_datasets']['ds1'], data_dir='test_dir')
    
    # Print it
    print(ds1)

def create_sample_hdf5(fname):
    with h5py.File(fname, 'w') as f:
        group1 = f.create_group(name='group1')
        ds1 = np.ones((3, 5))
        group1.create_dataset('ds1', data=ds1)

if __name__ == '__main__':
    main()