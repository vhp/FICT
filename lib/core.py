#!/usr/bin/env python3
#
#   Author: Vincent Perricone <vhp@fastmail.fm>
#   Date: 11/22/2017
#   Title: FICT
#   License: Released under "Simplified BSD License" see LICENSE file
#
import sys
import os
import json
from lib.fileobj import FileObj

def write_db(args, data):
    """Write the json database down to disk."""
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    try:
        with open(db_file, 'w') as json_db:
            json_db.write(data)
    except FileNotFoundError:
        print('Could not write to: {}'.format(db_file))

def read_db(args):
    """Read the json database from disk in read only mode"""
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    if os.path.isfile(db_file):
        with open(db_file, 'r') as json_db:
            try:
                data = json.load(json_db)
                return data
            except ValueError:
                return json.loads('[]')
    else:
        return json.loads('[]')

def init(args):
    """Initialize Fict project"""
    path = args['--fict-dir']
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        print("New FICT project created at: {}".format(path))
    else:
        print("FICT project already exists at: {}".format(path))

def walkfs(path):
    walked = []
    for root, directories, filenames in os.walk(path):
        for directory in directories:
            walked.append(('directory', os.path.join(os.path.abspath(root), directory)))
        for filename in filenames:
            walked.append(('file', os.path.join(os.path.abspath(root), filename)))
    return walked

def add(args):
    """Create new instances of FileObjs"""
    if os.path.isfile(args['<path>']):
        FileObj('file', args['<path>'], args['--hash-tool'])
    elif os.path.isdir(args['<path>']):
        for filetype, path in walkfs(args['<path>']):
            FileObj(filetype, path, args['--hash-tool'])
    else:
        sys.exit('Not a valid path for ADD function.')

def compute(args):
    """Compute hashes of all instances in FileObj.instances"""
    [obj.set_hash() for path, obj in FileObj.instances.items()]

def get_list(args):
    """Print list of all files and their hashes managed by Fict"""
    [print(obj.get_bundle()) for path, obj in FileObj.instances.items()]

def check(args):
    for path, obj in FileObj.instances.items():
        if not obj.check_integrity():
            print('Failed Integrity Check: {}'.format(obj.path))

def construct(args):
    """Reinitialize instances of FileObj via read_db"""
    try:
        for obj in read_db(args):
            FileObj.load(obj)
    except KeyError as error:
        sys.exit('JSON Key {} expected/unexpected in your fict_db. Check FileObJ schema'.format(error))
    except:
        print('fict_db reading exception: {}'.format(sys.exc_info()[0]))
        raise

def main(args):

    #Initialization
    if args['init']:
        init(args)
    elif not os.path.isdir(args['--fict-dir']):
        sys.exit('You must init a fict project first')

    #Construct instances of FileObj's for later use.
    construct(args)

    # Conditional operations after initialization and construction.
    if args['add']:
        add(args)
    elif args['compute']:
        compute(args)
    elif args['list']:
        get_list(args)
        sys.exit()
    elif args['check']:
        check(args)
        sys.exit()

    #Write out what we have to disk.
    write_db(args, json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4))


