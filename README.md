# h5_to_json

Convert HDF5 files to JSON format with the option of selectively separating out the large binary content of datasets as raw files affording the following advantages

* Because it is derived from the source code of [hdf5-json](https://github.com/HDFGroup/hdf5-json) from the HDFGroup, this project does not represent a new convention for JSON representation of HDF5. See [h5_to_json/hdf5-json-COPYING](h5_to_json/hdf5-json-COPYING).

* No information is lost in that `hdf5_to_json` followed by `json_to_hdf5` will ideally recover the the original file provided that the separated binary content is also made available.

* HDF5 files can be very large making storing or sharing files impractical. Separating out the binary content makes it possible to selectively share (or host on the web) parts of the file while retaining references to the original binary content.

* JSON is more universally readable/parsable than HDF5, particularly from JavaScript and other non-Python languages. It is far easier to work with JSON files in the context of web applications.

* Unlike with HDF5, the JSON storage is deterministic in that the file bytes are uniquely determined by the content. This allows to do diffs between hdf5.json files and to compute checksums and hashes that will reflect the content. Because the HDF5 files uses a complex internal structure for efficient I/O these properties are almost never satisfied for .hdf5 files.

* JSON is human readable using a text editor.

* Since binary array content may be stored outside the file in a raw format, it is possible to use range headers in HTML requests to retrieve slices of data, whereas slicing of arrays in .hdf5 files always requires an application layer doing the slicing. The greatly simplifies web applications that serve HDF5 content.

* Even when the content of datasets is separated out, the JSON file still contains all meta information and attributes of the dataset, including the data type and array dimensions (shape).

* It is possible to select which datasets get retained within the JSON file and which are separated out.

* Binary content that is separated out is intended to be stored in a content-addressable storage database, either on the local machine or in a remote database such as a [kachery](https://github.com/flatironinstitute/kachery).

## Installation

```
pip install --upgrade h5_to_json
```

Or a development installation (after cloning this repo and stepping into the directory):

```
pip install -e .
```

## Command line

Converting .hdf5 to .json:

```
> h5_to_json --help

usage: h5_to_json [-h] [--include-datasets]
                  [--include-dataset-names INCLUDE_DATASET_NAMES]
                  [--data-dir DATA_DIR]
                  h5_path [json_out_path [json_out_path ...]]

Serialize hdf5 file to JSON with option to separate out binary datasets

positional arguments:
  h5_path               Path to the hdf5 file
  json_out_path         Optional path to the output JSON file or use -- if not
                        provided, writes to stdout

optional arguments:
  -h, --help            show this help message and exit
  --include-datasets    Whether to include the binary data of datasets inside
                        the JSON content (not a great idea for large datasets
                        b/c the JSON serialization is inefficient)
  --include-dataset-names INCLUDE_DATASET_NAMES
                        Comma-separated list of names of datasets to include
                        in the JSON content
  --data-dir DATA_DIR, -d DATA_DIR
                        Directory for storing binary data by hash

```

Converting .json back to .hdf5:

```
> json_to_h5 --help

usage: json_to_h5 [-h] [--data-dir DATA_DIR] json_path h5_out_path

Restore hdf5 file from a JSON input

positional arguments:
  json_path             Path to the JSON file
  h5_out_path           Path to the hdf5 file

optional arguments:
  -h, --help            show this help message and exit
  --data-dir DATA_DIR, -d DATA_DIR
                        Directory where binary data is stored by hash
```

For example:

```
# Convert hdf5 to json
h5_to_json file1.h5 file1.h5.json --data-dir tmp_data

# Retrieve the hdf5 file, but the file bytes won't exactly match
json_to_h5 file1.h5.json file1_new.h5 --data-dir tmp_data

# Back to json a second time
h5_to_json file1_new.h5 file1_new.h5.json --data-dir tmp_data

# Now verify that the two .json files have the same content using meld (or diff)
meld file1.h5.json file1_new.h5.json
```

## Python API

There is also a Python API. For example:

```
import h5_to_json as h5j

# Represent hdf5 content in a dict
X = h5j.h5_to_dict('file1.h5', data_dir='tmp_data')

# Retrieve the hdf5 file (similar to the above command-line)
h5j.dict_to_h5(X, 'file1_new.h5', data_dir='tmp_data')
```

## License

See [COPYING](./COPYING)

## Authors

This project was derived from the source code of [hdf5-json](https://github.com/HDFGroup/hdf5-json) from the HDFGroup and was adapted by:

Jeremy Magland, Center for Computational Mathematics, Flatiron Institute
