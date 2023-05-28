#!/usr/bin/env python3
#
#   Author: Vincent Perricone <vhp@fastmail.fm>
#   Date: 11/2017
#   Title: FICT
#   License: Released under "Simplified BSD License" see LICENSE file
#
import uuid
import os
import logging
from datetime import datetime
from subprocess import Popen
from subprocess import PIPE

logger = logging.getLogger('fict')

class FileObj:
    """ Object structure """
    instances = {}

    def __init__(self, filetype, path, hash_bin):
        self.path = path
        #Add instance to instances dictionary. Duplicates wont be added.
        FileObj.instances.setdefault(self.path, self)
        self.filetype = None
        self.uuid = None
        self.status = 'pending'
        self.timestamp = None
        self.standard_hash = None
        self.standard_bin = "b2sum"
        self.hash_bin = hash_bin
        self.hash = None
        #Setup this instance
        self.set_uuid()
        self.set_filetype(filetype)


    def dump(self):
        """Dump elements for this object"""
        return {'path': self.path,
                'filetype': self.filetype,
                'uuid': self.uuid,
                'status':   self.status,
                'timestamp': str(self.timestamp),
                'standard_hash': self.standard_hash,
                'standard_bin': self.standard_bin,
                'hash_bin': self.hash_bin,
                'hash': self.hash}

    @classmethod
    def load(cls, json_dict):
        """Recreate instance of FileObj"""
        node = cls(json_dict['filetype'], json_dict['path'], json_dict['hash_bin'])
        node.path = json_dict['path']
        node.filetype = json_dict['filetype']
        node.uuid = json_dict['uuid']
        node.status = json_dict['status']
        node.timestamp = None if json_dict['timestamp'] else datetime.strptime(json_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

        node.standard_hash = json_dict['standard_hash']
        node.standard_bin = json_dict['standard_bin']
        node.hash_bin = json_dict['hash_bin']
        node.hash = json_dict['hash']
        return node

    def compute_hash(self, hash_bin):
        """Compute the hash of the file defined in self.path. Returns hash if file or string 'directory' if directory"""
        if not os.path.isdir(self.path):
            checksum_output = Popen([hash_bin, self.path], stdout=PIPE).communicate()[0].decode('utf-8').partition(' ')[0]
            return checksum_output.strip()
        else:
            return 'directory'

    def check_integrity(self):
        """Recheck integrity of file defined in self.path. Compare it to old/current hash return boolean with returns"""
        current_hash = self.hash
        new_hash = self.compute_hash(self.hash_bin)
        return bool(current_hash == new_hash)

    def set_filetype(self, filetype):
        """ Set the filetype for object """
        if filetype in ['file', 'directory']:
            self.filetype = filetype
        else:
            logger.error("Error: Wrong filetype ({}) for file".format(filetype))

    def set_hash(self):
        """ Call to compute the hash, and set the timestamp after """
        self.hash = self.compute_hash(self.hash_bin)
        self.standard_hash = self.compute_hash(self.standard_bin)
        self.set_timestamp()
        if self.hash:
            self.set_status("computed")

    def set_uuid(self):
        """ Set uuid of self """
        if self.uuid is None:
            self.uuid = str(uuid.uuid1())

    def set_status(self, status):
        """ Set task status of self """
        self.status = status
        if self.filetype in 'file':
            # Let's not print message when dealing with directory.
            logger.debug("- '{}' {} as\n\t {}".format(self.path, status, self.hash))

    def set_timestamp(self):
        """ Set creation stamp of task """
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def get_standard_hash(self):
        """ Return the standard_hash, usually Blake2 """
        return self.standard_hash

    def get_status(self):
        """ Return the instances status """
        return self.status

    def get_timestamp(self):
        """ Return the instances timestamp """
        return self.timestamp

    def get_path(self):
        """Return instances path"""
        return self.path

    def get_hash(self):
        """ Return the hash of the instances """
        return self.hash

    def get_hash_bin(self):
        """ Return the hash type or tool """
        return self.hash_bin

    def get_tuple(self):
        """ Return tuple containing (path, status, hash) """
        return (self.get_path(), self.get_status(), self.get_hash())
