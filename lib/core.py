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
import logging
import multiprocessing
from lib.fileobj import FileObj
from joblib import Parallel, delayed

num_cores = multiprocessing.cpu_count()
file_ignore_list = ['.fict', 'fict_db']

logger = logging.getLogger('fict')

def write_db(args, data):
    """Write the json database down to disk."""
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    logger.debug("writing db: {}".format(db_file))
    try:
        with open(db_file, 'w') as json_db:
            json_db.write(data)
    except FileNotFoundError:
        logger.error('Could not write to: {}'.format(db_file))

def read_db(args):
    """Read the json database from disk in read only mode"""
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    logger.debug("reading db: {}".format(db_file))
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
        logger.info("New FICT project created at: {}".format(path))
    else:
        logger.error("FICT project already exists at: {}".format(path))

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
    logger.debug("Adding path: {}".format(args['<path>']))
    if os.path.isfile(args['<path>']) and os.path.isfile(args['<path>']) not in file_ignore_list:
        FileObj('file', args['<path>'], args['--hash-tool'])
    elif os.path.isdir(args['<path>']):
        for filetype, path in walkfs(args['<path>']):
            if os.path.basename(os.path.normpath(path)) not in file_ignore_list:
                FileObj(filetype, path, args['--hash-tool'])
                logger.debug("Adding: {} ({})".format(path, filetype))

    else:
        sys.exit('Not a valid path for ADD function.')

def compute_runner(obj, args):
    obj.set_hash()
    logger.debug("Computed {} for file {}".format(obj.get_hash(), obj.get_path()))
    write_db(args, json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4))

def compute(args):
    """Compute hashes of all instances in FileObj.instances"""
    #[obj.set_hash() for path, obj in FileObj.instances.items()]
    # It's important to use prefer="threads" here as not using it uses processes and there's no ipc.
    Parallel(n_jobs=num_cores, prefer="threads")(delayed(compute_runner)(obj, args) for _, obj in FileObj.instances.items())

def get_list(args):
    """Print list of all files and their hashes managed by Fict"""
    [print(obj.get_bundle()) for path, obj in FileObj.instances.items()]

def check(args):
    for path, obj in FileObj.instances.items():
        if not obj.check_integrity():
            logger.error('Failed Integrity Check: {}'.format(obj.path))

def approve(args):
    get_list(args)
    if not args['--yes']:
        logger.error("\nYou must add -y/--yes command line option to: fict approve")
        sys.exit(2)
    else:
        [obj.set_status("approved") for _, obj in FileObj.instances.items()]
        write_db(args, json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4))

def construct(args):
    """Reinitialize instances of FileObj via read_db"""
    try:
        for obj in read_db(args):
            FileObj.load(obj)
    except KeyError as error:
        sys.exit('JSON Key {} expected/unexpected in your fict_db. Check FileObJ schema'.format(error))
    except:
        logger.error('fict_db reading exception: {}'.format(sys.exc_info()[0]))
        raise

def setup_logging(args):
    """Configure Logging to console"""
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    if args['--verbose']:
        logger.setLevel(logging.DEBUG)
        print(logging.getLevelName(logger.getEffectiveLevel()))
        logger.debug(args)

def main(args):

    #Initialization
    setup_logging(args)
    if args['init']:
        init(args)
    elif not os.path.isdir(args['--fict-dir']):
        sys.exit('You must init a fict project first')

    # Construct instances of FileObj's for  use later in run.
    construct(args)

    # Conditional operations after initialization and construction.
    if args['add']:
        add(args)
        compute(args)
        write_db(args, json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4))
    elif args['approve']:
        approve(args)
    elif args['recompute']:
        compute(args)
        write_db(args, json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4))
    elif args['list']:
        get_list(args)
        sys.exit()
    elif args['check']:
        check(args)
        sys.exit()
