import os
from .hdf5db import Hdf5db
from .h5tojson import DumpJson

def h5_to_dict(
        h5_path,
        *,
        include_datasets=False,
        include_dataset_names=[],
        data_dir=None,
        use_kachery=False
    ):
        """
        Generate a temporary filename to avoid problems with trying to create a dbfile
        in a read-only directory.  (See: https://github.com/HDFGroup/h5serv/issues/37)
        """
        if data_dir is not None:
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)

        import tempfile
        def getTempFileName():
            f = tempfile.NamedTemporaryFile(delete=False)
            f.close()
            return f.name

        if not os.path.exists('_datasets'):
            os.mkdir('_datasets')

        dbFilename = getTempFileName()
        options = dict(
            include_datasets=include_datasets,
            include_dataset_names=include_dataset_names,
            data_dir=data_dir,
            use_kachery=use_kachery
        )
        with Hdf5db(h5_path, dbFilePath=dbFilename, readonly=True) as db:
            dumper = DumpJson(db, options=options)
            X = dumper.toDict()
        return X