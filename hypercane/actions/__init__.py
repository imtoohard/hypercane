import logging
import sys
import argparse
import pickle

from ..version import __useragent__

def get_logger(appname, loglevel, logfile):

    logger = logging.getLogger(appname)

    if logfile == sys.stdout:
        logging.basicConfig( 
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=loglevel)
    else:
        logging.basicConfig( 
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=loglevel,
            filename=logfile)

    return logger

def calculate_loglevel(verbose=False, quiet=False):
  
    # verbose trumps quiet
    if verbose:
        return logging.DEBUG

    if quiet:
        return logging.WARNING

    return logging.INFO

def add_default_args(parser):

    parser.add_argument('-l', '--logfile', dest='logfile',
        default=sys.stdout,
        help="The path to a logging file. The log is printed to screen by default.")

    parser.add_argument('-v', '--verbose', dest='verbose',
        action='store_true',
        help="This will raise the logging level to debug for more verbose output")

    parser.add_argument('-q', '--quiet', dest='quiet',
        action='store_true',
        help="This will lower the logging level to only show warnings or errors")

    parser.add_argument('-cs', '--cache-storage', dest='cache_storage',
        default='/tmp/hypercane-cache.sqlite',
        help="A SQLite file for use as a cache."
    )

    parser.add_argument('--version', action='version', 
        version="{}".format(__useragent__))

    return parser

def add_input_args(parser):

    parser.add_argument('-i', help="the input type and identifier, separated by equals (=) examples: -i archiveit=8788 or -i timemaps=timemap-file.txt,https://archive.example.com/timemap/http://example2.com; supported input types are archiveit, timemap, mementos, original-resources", dest='input_type', required=True, type=process_collection_input_types)

    parser.add_argument('-o', required=True, help="the file to which we write output", dest='output_filename')

    parser.add_argument('--crawl-depth', '--depth', required=False, help="the number of levels to use in the crawl", dest='crawl_depth', default=1, type=int)

    return parser

def process_collection_input_types(input_argument):

    supported_input_types = [
        "archiveit",
        "timemaps",
        "mementos",
        "original-resources",
        "warcs"
    ]

    if '=' not in input_argument:
        raise argparse.ArgumentTypeError(
            "no required argument supplied for input type {}\n\n"
            "Examples:\n"
            "for an Archive-It collection use something like\n"
            "-i archiveit=3639"
            .format(input_argument)
            )

    input_type, argument = input_argument.split('=') 

    if input_type not in supported_input_types:
        raise argparse.ArgumentTypeError(
            "{} is not a supported input type, supported types are {}".format(
                input_type, list(supported_input_types)
                )
            )

    return input_type, argument
