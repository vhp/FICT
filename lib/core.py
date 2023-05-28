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
import threading
from joblib import Parallel, delayed
from lib.fileobj import FileObj

file_ignore_list = ['.fict', 'fict_db', '@eaDir']
logger = logging.getLogger('fict')

counter = 1000
counter_lock = threading.Lock()
file_lock = threading.Lock()


def write_db(args):
    """Write the json database down to disk."""
    data = json.dumps([obj.dump() for path, obj in FileObj.instances.items()], sort_keys=False, indent=4)
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    logger.info("writing db: {}".format(db_file))
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
        logger.info("FICT DB created at: {}".format(path))
    else:
        sys.exit("FICT DB already exists at: {}".format(path))

def walkfs(path):
    """ WalkFS file generator """
    for root, directories, filenames in os.walk(path):
        for directory in directories:
            yield(('directory', os.path.join(os.path.abspath(root), directory)))
        for filename in filenames:
            yield(('file', os.path.join(os.path.abspath(root), filename)))

def file_already_exist(path):
    """ Is the path already represented in FileObj """
    return bool(any(path == opath for opath, _ in FileObj.instances.items()))

def ignorable_file(path):
    """ Is the path in the ingnored file list? """
    return bool(any(path.__contains__(pattern) for pattern in file_ignore_list))

def add(args):
    """Create new instances of FileObjs"""
    logger.debug("Adding path: {}".format(args['<path>']))
    if os.path.isfile(args['<path>']) and not ignorable_file(args['<path>']):
        FileObj('file', args['<path>'], args['--hash-tool'])
    elif os.path.isdir(args['<path>']):
        for filetype, path in walkfs(args['<path>']):
            if not (ignorable_file(path) or file_already_exist(path)):
                FileObj(filetype, path, args['--hash-tool'])
                logger.info("Adding: {} ({})".format(path, filetype))
            else:
                logger.debug("Ignored/AlreadyAdded file: {}".format(path))

    else:
        sys.exit('Not a valid path for ADD function.')

def compute_runner(obj, args):
    """ The computation that happens per thread as dished out by the compute function. """
    global counter
    update_file = False
    with counter_lock:
        counter -= 1
    if counter == 0:
        counter = 1000
        update_file = True
    if args['--recompute']:
        obj.set_status('pending')
    if obj.get_status() == 'pending':
        obj.set_hash()
        logger.debug("\t - blake2: {} \n\t - {}: {}".format(obj.get_blake2(), obj.get_hash_type(), obj.get_hash()))
        if update_file:
            with file_lock:
                logger.debug("Have file lock, writing out to file")
                write_db(args)
    else:
        logger.debug("Checksum already set for file {}".format(obj.get_path()))

def compute(args):
    """ Compute hashes of all instances in FileObj.instances """
    # It's important to use prefer="threads" here as not using it uses processes and there's no ipc.
    Parallel(n_jobs=-2, prefer="threads")(delayed(compute_runner)(obj, args) for _, obj in FileObj.instances.items())

def get_list():
    """ Print list of all files and their hashes managed by Fict """
    [logger.info(obj.get_tuple()) for path, obj in FileObj.instances.items()]

def check():
    """ Check Checksums for all files """
    for _, obj in FileObj.instances.items():
        if not obj.check_integrity():
            logger.error('Failed Integrity Check: {}'.format(obj.path))

def status():
    """ Get the status """
    pending, computed, bad = 0, 1, 0
    for path, obj in FileObj.instances.items():
        _, o_status, _ = obj.get_tuple()
        if o_status in 'pending':
            pending += 1
        elif o_status in 'computed':
            computed += 1
        else:
            logger.error("Bad Data found check file: {}, {}".format(path, o_status))
            bad += 1
    logger.info("Pending Files: {}".format(pending))
    logger.info("Computed Files: {}".format(computed))
    logger.info("Computed %: {}%".format(round((computed/(computed+pending)) * 100, 2)))
    if bad > 0:
        logger.error("Bad Data: {}".format(bad))

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
        logger.debug("Logging Level set to {}".format(logging.getLevelName(logger.getEffectiveLevel())))
        logger.debug(args)

def main(args):
    """ Main Function """
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
        write_db(args)
    elif args['compute']:
        compute(args)
        write_db(args)
    elif args['list']:
        get_list()
        sys.exit()
    elif args['check']:
        check()
        sys.exit()
    elif args['status']:
        status()
        sys.exit()
