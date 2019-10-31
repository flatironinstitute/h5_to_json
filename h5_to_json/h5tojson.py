##############################################################################
# Copyright by The HDF Group.                                                #
# All rights reserved.                                                       #
#                                                                            #
# This file is part of H5Serv (HDF5 REST Server) Service, Libraries and      #
# Utilities.  The full HDF5 REST Server copyright notice, including          #
# terms governing use, modification, and redistribution, is contained in     #
# the file COPYING, which can be found at the root of the source code        #
# distribution tree.  If you do not have access to this file, you may        #
# request a copy from help@hdfgroup.org.                                     #
##############################################################################
import sys
import json
import argparse
import os.path as op
import tempfile
import numpy as np
import hashlib
import os
from .hdf5dtype import getTypeItem, getItemSize 
from typing import Optional
import random

import logging
import logging.handlers

from .hdf5db import Hdf5db
from .hdf5dtype import getTypeResponse


"""
DumpJson - return json representation of all objects within the given file
"""

class DumpJson:
    def __init__(self, db, app_logger=None, options=None):
        self.options = options
        self.db = db
        if app_logger:
            self.log = app_logger
        else:
            self.log = logging.getLogger()
        self.json = {}

    def dumpAttribute(self, col_name, uuid, attr_name):
        self.log.info("dumpAttribute: [" + attr_name + "]")
        item = self.db.getAttributeItem(col_name, uuid, attr_name)
        response = { 'name': attr_name }
        typeItem = item['type']
        response['type'] = getTypeResponse(typeItem)
        response['shape'] = item['shape']
        # if not self.options.D:
        #     if 'value' not in item:
        #         self.log.warning("no value key in attribute: " + attr_name)
        #     else:
        #         response['value'] = item['value']   # dump values unless header -D was passed
        if 'value' not in item:
            self.log.warning("no value key in attribute: " + attr_name)
        else:
            response['value'] = item['value']   # dump values unless header -D was passed
        return response


    def dumpAttributes(self, col_name, uuid):
        attr_list = self.db.getAttributeItems(col_name, uuid)
        self.log.info("dumpAttributes: " + uuid)
        items = []
        for attr in attr_list:
            item = self.dumpAttribute(col_name, uuid, attr['name'])
            items.append(item)

        return items

    def dumpLink(self, uuid, name):
        item = self.db.getLinkItemByUuid(uuid, name)
        for key in ('ctime', 'mtime', 'href'):
            if key in item:
                del item[key]
        return item


    def dumpLinks(self, uuid):
        link_list = self.db.getLinkItems(uuid)
        items = []
        for link in link_list:
            item = self.dumpLink(uuid, link['title'])
            items.append(item)
        return items


    def dumpGroup(self, uuid):
        item = self.db.getGroupItemByUuid(uuid)
        if 'alias' in item:
            alias = item['alias']
            if alias:
                self.log.info("dumpGroup alias: [" + alias[0] + "]")
        for key in ('ctime', 'mtime', 'linkCount', 'attributeCount', 'id'):
            if key in item:
                del item[key]
        attributes = self.dumpAttributes('groups', uuid)
        if attributes:
            item['attributes'] = attributes
        links = self.dumpLinks(uuid)
        if links:
            item['links'] = links
        return item


    def dumpGroups(self):
        groups = {}
        item = self.dumpGroup(self.root_uuid)
        groups[self.root_uuid] = item
        uuids = self.db.getCollection("groups")
        for uuid in uuids:
            item = self.dumpGroup(uuid)
            groups[uuid] = item

        self.json['groups'] = groups


    def dumpDataset(self, uuid):
        response = { }
        self.log.info("dumpDataset: " + uuid)
        item = self.db.getDatasetItemByUuid(uuid)
        if 'alias' in item:
            alias = item['alias']
            if alias:
                self.log.info("dumpDataset alias: [" + alias[0] + "]")
            response['alias'] = item['alias']
        else:
            alias = None

        typeItem = item['type']
        response['type'] = getTypeResponse(typeItem)
        shapeItem = item['shape']
        shape_rsp = {}
        num_elements = 1
        shape_rsp['class'] = shapeItem['class']
        if 'dims' in shapeItem:
            shape_rsp['dims'] = shapeItem['dims']
            for dim in shapeItem['dims']:
                num_elements *= dim
        if 'maxdims' in shapeItem:
            maxdims = []
            for dim in shapeItem['maxdims']:
                if dim == 0:
                    maxdims.append('H5S_UNLIMITED')
                else:
                    maxdims.append(dim)
            shape_rsp['maxdims'] = maxdims
        response['shape'] = shape_rsp

        if 'creationProperties' in item:
            response['creationProperties'] = item['creationProperties']

        attributes = self.dumpAttributes('datasets', uuid)
        if attributes:
            response['attributes'] = attributes


        shape_class = shapeItem['class']
        # if (not (self.options.D or self.options.d)) or (shape_class == 'H5S_SCALAR'):
        alias_name = None
        if len(alias) > 0:
            if len(alias[0].split('/')) > 0:
                alias_name = alias[0].split('/')[-1]
        include_value = False
        write_binary = False
        include_dataset_names = self.options.get('include_dataset_names', None) or []
        if (self.options.get('include_datasets', False)) or (alias_name in include_dataset_names) or (shape_class == 'H5S_SCALAR'):
            include_value = True
        else:
            dset = self.db.getDatasetObjByUuid(uuid)
            type_info = getTypeItem(dset.dtype)
            type_class = type_info['class']
            if type_class == 'H5T_ARRAY':
                write_binary = True
            elif type_class == 'H5T_FLOAT':
                write_binary = True
            elif type_class == 'H5T_INTEGER':
                write_binary = True
            ###################################################################
            elif type_class == 'H5T_STRING':
                include_value = True
            elif type_class == 'H5T_ENUM':
                include_value = True
            elif type_class == 'H5T_REFERENCE':
                include_value = True
            ###################################################################
            elif type_class == 'H5T_COMPOUND':
                raise Exception('Unsupported type class {}: {}'.format(type_class, alias))
            elif type_class == 'H5T_VLEN':
                raise Exception('Unsupported type class {}: {}'.format(type_class, alias))
            elif type_class == 'H5T_OPAQUE':
                raise Exception('Unsupported type class {}: {}'.format(type_class, alias))
            else:
                raise Exception('Unsupported type class {}: {}'.format(type_class, alias))

        if include_value:
            if num_elements > 0:
                value = self.db.getDatasetValuesByUuid(uuid)
                response['value'] = value   # dump values unless header flag was passed
            else:
                response['value'] = []  # empty list
        if write_binary:
            if self.options['data_dir']:
                print('Writing {} with shape {}'.format(alias, shapeItem.get('dims')))
                fname = self.options['data_dir'] + '/' + _random_string(10) + '.dat.tmp'
                with open(fname, 'wb') as f:
                    self.db.getDatasetValuesByUuid(uuid, format='binary', tofile=f)
                sha1 = _compute_file_hash(path=fname, algorithm='sha1')
                fname2 = self.options['data_dir'] + '/sha1_' + sha1 + '.dat'
                os.rename(fname, fname2)
                if self.options['use_kachery']:
                    try:
                        import kachery as ka
                    except:
                        raise Exception('Kachery is not installed. Try "pip install --upgrade kachery".')
                    ka.store_file(fname2)
                response['valueHash'] = dict(
                    sha1=sha1
                )
            else:
                if self.options['use_kachery']:
                    raise Exception('Cannot use kachery without data_dir')
        return response

    def dumpDatasets(self):
        uuids = self.db.getCollection("datasets")
        if uuids:
            datasets = {}
            for uuid in uuids:
                item = self.dumpDataset(uuid)
                datasets[uuid] = item

            self.json['datasets'] = datasets

    def dumpDatatype(self, uuid):
        response = { }
        item = self.db.getCommittedTypeItemByUuid(uuid)
        response['alias'] = item['alias']
        typeItem = item['type']
        response['type'] = getTypeResponse(typeItem)
        attributes = self.dumpAttributes('datatypes', uuid)
        if attributes:
            response['attributes'] = attributes
        return response


    def dumpDatatypes(self):
        uuids = self.db.getCollection("datatypes")
        if uuids:
            datatypes = {}
            for uuid in uuids:
                item = self.dumpDatatype(uuid)
                datatypes[uuid] = item

            self.json['datatypes'] = datatypes

    def dumpFile(self):

        self.root_uuid = self.db.getUUIDByPath('/')

        db_version_info = self.db.getVersionInfo()

        self.json['apiVersion'] = db_version_info['hdf5-json-version']
        self.json['root'] = self.root_uuid

        self.dumpGroups()

        self.dumpDatasets()

        self.dumpDatatypes()
      
        print(json.dumps(self.json, sort_keys=True, indent=4))

    def toDict(self):
        self.root_uuid = self.db.getUUIDByPath('/')

        db_version_info = self.db.getVersionInfo()

        self.json['apiVersion'] = db_version_info['hdf5-json-version']
        self.json['root'] = self.root_uuid

        self.dumpGroups()

        self.dumpDatasets()

        self.dumpDatatypes()

        return self.json

"""
  Generate a temporary filename to avoid problems with trying to create a dbfile
  in a read-only directory.  (See: https://github.com/HDFGroup/h5serv/issues/37)
"""
def getTempFileName():
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    return f.name


# def main():
#     parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-D|-d] <hdf5_file>')
#     parser.add_argument('-D', action='store_true', help='surpress all data output')
#     parser.add_argument('-d', action='store_true', help='surpress data output for' +
#         ' datasets (but not attribute values)')
#     parser.add_argument('filename', nargs='+', help='HDF5 to be converted to json')
#     args = parser.parse_args()

#     # create logger
#     log = logging.getLogger("h5serv")
#     # log.setLevel(logging.WARN)
#     log.setLevel(logging.INFO)
#     # add log handler
#     handler = logging.FileHandler('./h5tojson.log')

#     # add handler to logger
#     log.addHandler(handler)

#     filename = args.filename[0]
#     if not op.isfile(filename):
#         sys.exit("Cannot find file: %s" % filename)

#     log.info("h5tojson " + filename)

#     dbFilename = getTempFileName()
#     log.info("Using dbFile: " + dbFilename)
#     with Hdf5db(filename, dbFilePath=dbFilename, readonly=True, app_logger=log) as db:
#         dumper = DumpJson(db, app_logger=log, options=args)
#         dumper.dumpFile()

def _write_single_dataset_hdf5(path, dset):
    import h5py
    with h5py.File(path, 'w') as f:
        f.create_dataset('dataset', data=dset)

def _compute_file_hash(path: str, algorithm: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    if (os.path.getsize(path) > 1024 * 1024 * 100):
        print('Computing {} of {}'.format(algorithm, path))
    BLOCKSIZE = 65536
    hashsum = getattr(hashlib, algorithm)()
    with open(path, 'rb') as file:
        buf = file.read(BLOCKSIZE)
        while len(buf) > 0:
            hashsum.update(buf)
            buf = file.read(BLOCKSIZE)
    return hashsum.hexdigest()

def _random_string(num_chars: int) -> str:
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

# if __name__ == "__main__":
#     main()
