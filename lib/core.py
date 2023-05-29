#!/usr/bin/env python3
#
#   Author: Vincent Perricone <vhp@fastmail.fm>
#   Date: 11/22/2017
#   Title: FICT
#   License: Released under "Simplified BSD License" see LICENSE file
#
"""
Functions relating to the manipulation of Fileobj's.
"""
import json
import logging
import os
import re
import sys
import threading
from alive_progress import alive_bar, alive_it
from joblib import Parallel, delayed
from lib.fileobj import FileObj

file_ignore_list = ['.fict', 'fict_db', '@eaDir']
logger = logging.getLogger('fict')

counter = 1000
counter_lock = threading.Lock()
FILE_LOCK = threading.Lock()


def write_db(args):
    """Write the json database down to disk."""
    data = json.dumps([obj.dump() for path, obj in FileObj.instances.items()],
                      sort_keys=False, indent=4)
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    logger.debug("writing out db @ %s", db_file)
    try:
        with open(db_file, 'w') as json_db:
            json_db.write(data)
    except FileNotFoundError:
        logger.error('Could not write to: %s', db_file)

def read_db(args):
    """Read the json database from disk in read only mode"""
    db_file = os.path.abspath('{}/{}'.format(args['--fict-dir'], args['--fict-db-name']))
    logger.debug("reading db: %s", db_file)
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
        logger.info("FICT DB created at: %s", path)
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
    logger.debug("Adding path: %s", args['<path>'])
    if os.path.isfile(args['<path>']) and not ignorable_file(args['<path>']):
        FileObj('file', args['<path>'], args['--hash-tool'])
    elif os.path.isdir(args['<path>']):
        for filetype, path in walkfs(args['<path>']):
            if not (ignorable_file(path) or file_already_exist(path)):
                FileObj(filetype, path, args['--hash-tool'])
                logger.debug("Adding: %s (%s)", path, filetype)
            else:
                logger.debug("Ignored/AlreadyAdded file: %s", path)
    else:
        sys.exit('Not a valid path for add')

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
        logger.debug("\t - blake2: %s \n\t - %s: %s", obj.get_standard_hash(), obj.get_hash_bin(), obj.get_hash())
        if update_file:
            with FILE_LOCK:
                write_db(args)
    else:
        logger.debug("Checksum already set for file %s", obj.get_path())

def compute(args):
    """ Compute hashes of all instances in FileObj.instances """
    # The alive_it helper here automatically gets a count and gives us a progress bar.
    # The progress bar is not always perfect.
    #
    bar_instances = alive_it(FileObj.instances.items(), enrich_print=False)

    # It's important to use prefer="threads" here as not using it uses processes and there's no ipc.
    # Here we use n_jobs=-2 as to ask the system for an acceptable number based on cpu. Using a higher number just
    # creates high cpu time for iowait and software interrupts.
    #
    Parallel(n_jobs=-2, prefer="threads")(delayed(compute_runner)(obj, args) for _, obj in bar_instances)

def get_list():
    """ Print list of all files and their hashes managed by Fict """
    [logger.info(obj.get_tuple()) for path, obj in FileObj.instances.items()]

def searched_instances(args):
    """Search instances in FileObj.instances.items() and return the ones that don't match args['<path>']"""
    re_pattern = re.compile('^{}'.format(args['<path>']))
    filtered_objects = [(path, obj) for path, obj in FileObj.instances.items() if re_pattern.match(obj.path)]
    logger.debug("%s of %s total instances match inputted pattern '%s'", len(filtered_objects), len(FileObj.instances.items()), args['<path>'])
    if len(filtered_objects) > 0:
        return filtered_objects
    return FileObj.instances.items()

def check(args):
    """ Check Checksums for all files """
    instances = searched_instances(args)
    with alive_bar(len(instances), enrich_print=False) as bar:
        for _, obj in instances:
            if not obj.check_integrity(mode='standard'):
                logger.error('std_FAIL[%s]: %s', obj.standard_bin, obj.path)
                if not obj.check_integrity(mode='secondary'):
                    logger.error('2nd_FAIL[%s]: %s', obj.hash_bin, obj.path)
                else:
                    logger.info('%s: \n\tPassed secondary integrity check (%s) but failed first (%s)', obj.path, obj.hash_bin, obj.standard_bin)
            else:
                logger.debug('PASS[%s]: %s', obj.standard_bin, obj.path)
            bar() #call bar function to increment progress bar

def status():
    """ Printout the status """
    pending, computed, percent, bad = 0, 0, 0, 0
    for path, obj in FileObj.instances.items():
        _, o_status, _ = obj.get_tuple()
        if o_status in 'pending':
            pending += 1
        elif o_status in 'computed':
            computed += 1
        else:
            logger.error("Bad Data found check file: %s, %s", path, o_status)
            bad += 1
    logger.info("Pending Files: %s", pending)
    logger.info("Computed Files: %s", computed)
    try:
        percent = round(computed/(computed + pending) * 100, 2)
    except ZeroDivisionError:
        logger.info("Computed %%: %s%%", 0)
    else:
        logger.info("Computed %%: %s%%", percent)
    if bad > 0:
        logger.error("Bad Data: %s", bad)

def construct(args):
    """Reinitialize instances of FileObj via read_db"""
    try:
        for obj in read_db(args):
            FileObj.load(obj)
    except KeyError as error:
        sys.exit('JSON Key {} expected/unexpected in your fict_db. Check FileObJ schema'.format(error))
    except:
        logger.error('fict_db reading exception: %s', sys.exc_info()[0])
        raise

def setup_logging(args):
    """Configure Logging to console"""
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    if args['--verbose']:
        logger.setLevel(logging.DEBUG)
        logger.debug("Logging Level set to %s", logging.getLevelName(logger.getEffectiveLevel()))
        logger.debug(args)

def main(args):
    """ Main Function """
    #Initialization
    setup_logging(args)
    if args['init']:
        init(args)
    elif not os.path.isdir(args['--fict-dir']):
        sys.exit("You must initialize a fict project first, 'fict init'")

    # Construct FileObj instances
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
        check(args)
        sys.exit()
    elif args['status']:
        status()
        sys.exit()
