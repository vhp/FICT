#!/usr/bin/env python3
#
#   Author: Vincent Perricone <vhp@fastmail.fm>
#   Date: 11/2017
#   Title: FICT
#   License: Released under "Simplified BSD License" see LICENSE file
#
import uuid
import json
import os
import sys
import logging
from datetime import datetime
from subprocess import Popen
from subprocess import PIPE

logger = logging.getLogger('fict')

class FileObj:
    instances = {}

    def __init__(self, filetype, path, hash_type):
        self.path = path
        #Add instance to instances dictionary. Duplicates wont be added.
        FileObj.instances.setdefault(self.path, self)
        self.filetype = None
        self.uuid = None
        self.status = 'pending'
        self.timestamp = None
        self.hash_type = hash_type
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
                'hash_type': self.hash_type,
                'hash': self.hash}

    @classmethod
    def load(cls, json_dict):
        """Recreate instance of FileObj"""
        node = cls(json_dict['filetype'], json_dict['path'], json_dict['hash_type'])
        node.path = json_dict['path']
        node.filetype = json_dict['filetype']
        node.uuid = json_dict['uuid']
        node.status = json_dict['status']
        node.timestamp = None if json_dict['timestamp'] else datetime.strptime(json_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
        node.hash_type = json_dict['hash_type']
        node.hash = json_dict['hash']
        return node

    def compute_hash(self):
        """Compute the hash of the file defined in self.path. Returns hash if file or string 'directory' if directory"""
        if not os.path.isdir(self.path):
            checksum_output = Popen([self.hash_type, self.path], stdout=PIPE).communicate()[0].decode('utf-8').partition(' ')[0]
            return checksum_output.strip()
        else:
            return 'directory'

    def check_integrity(self):
        """Recheck integrity of file defined in self.path. Compare it to old/current hash return boolean with returns"""
        current_hash = self.hash
        new_hash = self.compute_hash()
        if current_hash == new_hash:
            return True
        else:
            return False

    def set_filetype(self, filetype):
        if filetype in ['file', 'directory']:
            self.filetype = filetype
        else:
            logger.error("Error: Wrong filetype ({}) for file".format(filetype, self.path))

    def set_hash(self):
        """Call to compute the hash, and set the timestamp after"""
        self.hash = self.compute_hash()
        self.set_timestamp()

    def set_uuid(self):
        """set uuid of self"""
        if self.uuid == None:
            self.uuid = str(uuid.uuid1())

    def set_status(self, status_value):
        """set task status of self"""
        self.status = status_value

    def set_timestamp(self):
        """set creation stamp of task"""
        if self.timestamp == None:
            self.timestamp = datetime.now()

    def get_status(self):
        """Return the instances status"""
        return self.status

    def get_timestamp(self):
        """Return the instances timestamp"""
        return self.timestamp

    def get_path(self):
        """Return instances path"""
        return self.path

    def get_hash(self):
        """Return the hash of the instances"""
        return self.hash

    def get_bundle(self):
        """Return bundles (path, hash)"""
        return '{},{},{}'.format(self.get_path(), self.get_status(), self.get_hash())
