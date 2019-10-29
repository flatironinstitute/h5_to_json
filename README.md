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



