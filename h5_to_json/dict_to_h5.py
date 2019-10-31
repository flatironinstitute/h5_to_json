import os
import h5py
from .hdf5db import Hdf5db
from .jsontoh5 import Writeh5

def dict_to_h5(
        obj,
        h5_path,
        *,
        data_dir=None,
        use_kachery=False
    ):
        if "root" not in obj:
            raise Exception("no root key in input file")
        root_uuid = obj["root"]
        
        if os.path.exists(h5_path):
            os.remove(h5_path)

        # create the file, will raise IOError if there's a problem
        Hdf5db.createHDF5File(h5_path) 

        with Hdf5db(h5_path, root_uuid=root_uuid, update_timestamps=False) as db:
            h5writer = Writeh5(db, obj, data_dir=data_dir, use_kachery=use_kachery)
            h5writer.writeFile()

        # open with h5py and remove the _db_ group
        # Note: this will delete any anonymous (un-linked) objects
        f = h5py.File(h5_path, 'a')
        if "__db__" in f:
            del f["__db__"]
        f.close()
