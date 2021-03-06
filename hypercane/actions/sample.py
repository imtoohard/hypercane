import sys
import hypercane.errors

def run_sample_with(parser, args, algorithm_name, algorithm_script):

    from sys import platform
    import errno

    if platform == "win32":
        print("Error: AlNoamany's Algorithm can only be executed via `hc sample` on Linux or macOS. Please see documentation for how to execute it on Windows and submit an issue to our Issue Tracker if you need Windows support.")
        sys.exit(errno.ENOTSUP)

    import argparse
    import subprocess
    import os
    import shlex
    from datetime import datetime
    from hypercane.actions import add_input_args, add_default_args
    from hypercane.actions import get_logger, calculate_loglevel
    from hypercane.utils import get_web_session, save_resource_data
    from hypercane.identify import discover_resource_data_by_input_type, \
        discover_timemaps_by_input_type

    parser = add_input_args(parser)

    parser = add_default_args(parser)

    runtime_string = "{}".format(datetime.now()).replace(' ', 'T')

    parser.add_argument('--working-directory', required=False,
        help="the directory to which this application should write output",
        default="/tmp/hypercane/working/{}".format(runtime_string),
        dest='working_directory')

    args = parser.parse_args(args)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    logger.info("Executing the {} algorithm with working directory {}".format(
        algorithm_name, args.working_directory))

    logger.info("Using cache storage of '{}'".format(args.cache_storage))

    os.makedirs(args.working_directory, exist_ok=True)

    logger.info("executing algorithm script from {}".format(algorithm_script))

    logger.info("args: {}".format(args))

    if type(args.logfile) != str:
        args.logfile = ""

    if args.errorfilename is None:
        args.errorfilename = ""

    other_arglist = []

    for argname, argvalue in vars(args).items():
        if argname not in [
            'input_type',
            'input_arguments',
            'cache_storage',
            'working_directory',
            'output_filename',
            'logfile',
            'errorfilename'
        ]:
            if argvalue is not False:
                other_arglist.append( "--{} {}".format(
                    argname.replace('_', '-'), argvalue
                ) )

    other_args = '"' + " ".join(other_arglist) + '"'

    logger.info("using other arguments: {}".format(other_args))

    cp = subprocess.run(
        [
            "/bin/bash",
            algorithm_script,
            args.input_type,
            args.input_arguments,
            args.cache_storage,
            args.working_directory,
            args.output_filename,
            args.logfile,
            args.errorfilename,
            other_args
        ]
    )

    if cp.returncode != 0:
        logger.critical("An error was encountered while executing the {} algorithm".format(algorithm_name))
    else:
        logger.info("Done executing the {} algorithm".format(algorithm_name))

    return args

def run_sample_with_dsa1(parser, args):

    from sys import platform
    import errno

    if platform == "win32":
        print("Error: AlNoamany's Algorithm can only be executed via `hc sample` on Linux or macOS. Please see documentation for how to execute it on Windows and submit an issue to our Issue Tracker if you need Windows support.")
        sys.exit(errno.ENOTSUP)

    import argparse
    import subprocess
    import os
    import shlex
    from datetime import datetime
    from hypercane.actions import add_input_args, add_default_args
    from hypercane.actions import get_logger, calculate_loglevel
    from hypercane.utils import get_web_session, save_resource_data
    from hypercane.identify import discover_resource_data_by_input_type, \
        discover_timemaps_by_input_type

    parser = add_input_args(parser)

    parser = add_default_args(parser)

    runtime_string = "{}".format(datetime.now()).replace(' ', 'T')

    parser.add_argument('--working-directory', required=False,
        help="the directory to which this application should write output",
        default="/tmp/hypercane/working/{}".format(runtime_string),
        dest='working_directory')

    args = parser.parse_args(args)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    logger.info("Executing DSA1 (AlNoamany's) algorithm with working directory {}".format(args.working_directory))

    os.makedirs(args.working_directory, exist_ok=True)

    scriptdir = os.path.dirname(os.path.realpath(__file__))

    algorithm_script = "{}/../packaged_algorithms/dsa1.sh".format(scriptdir)

    logger.info("executing algorithm script from {}".format(algorithm_script))

    if type(args.logfile) != str:
        args.logfile = ""

    cp = subprocess.run(
        [
            "/bin/bash",
            algorithm_script,
            args.input_type,
            args.input_arguments,
            args.cache_storage,
            args.working_directory,
            args.output_filename,
            args.logfile
        ]
    )

    if cp.returncode != 0:
        logger.critical("An error was encountered while executing DSA1 (AlNoamany's) algorithm")
    else:
        logger.info("Done executing DSA1 (AlNoamany's) algorithm")

    return args

def sample_with_dsa1(args):

    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Sample URI-Ms from a web archive collection with DSA1 (AlNoamany's) algorithm.",
        prog="hc sample dsa1"
    )

    parser.add_argument('--memento-damage-url', dest='memento_damage_url',
        default=None,
        help="The URL of the Memento-Damage service to use for scoring."
    )

    algorithm_script = "{}/../packaged_algorithms/dsa1.sh".format(
        os.path.dirname(os.path.realpath(__file__))
    )

    # run_sample_with_dsa1(parser, args)
    run_sample_with(parser, args, "DSA1", algorithm_script)

def sample_with_alnoamany(args):

    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Sample URI-Ms from a web archive collection with DSA1 (AlNoamany's) algorithm.",
        prog="hc sample alnoamany"
        )

    parser.add_argument('--memento-damage-url', dest='memento_damage_url',
        default=None,
        help="The URL of the Memento-Damage service to use for ranking."
    )

    algorithm_script = "{}/../packaged_algorithms/dsa1.sh".format(
        os.path.dirname(os.path.realpath(__file__))
    )

    # run_sample_with_dsa1(parser, args)
    run_sample_with(parser, args, "AlNoamany", algorithm_script)

def sample_with_filtered_random(args):

    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Sample URI-Ms from a web archive collection by filtering off-topic mementos, filtering near-duplicates, and then sampling k of the remainder, randomly.",
        prog="hc sample filtered-random"
        )

    algorithm_script = "{}/../packaged_algorithms/filtered_random.sh".format(
         os.path.dirname(os.path.realpath(__file__))
    )

    parser.add_argument('-k', required=False, help="the number of items to sample", default=28, dest='k')

    run_sample_with(parser, args, "Filtered Random", algorithm_script)

def sample_with_true_random_args(args):

    import argparse

    from hypercane.actions import add_input_args, add_default_args

    parser = argparse.ArgumentParser(
        description="Sample random URLs from a web archive collection.",
        prog="hc sample true-random"
        )

    parser = add_input_args(parser)

    parser.add_argument('-k', '--k', required=False, help="the number of items to sample", default=28, dest='sample_count')

    parser = add_default_args(parser)

    args = parser.parse_args(args)

    return args

def sample_with_true_random(args):

    from hypercane.sample.true_random import select_true_random
    from hypercane.actions import get_logger, calculate_loglevel
    from hypercane.utils import get_web_session, save_resource_data
    from hypercane.identify import discover_resource_data_by_input_type, \
        discover_mementos_by_input_type

    args = sample_with_true_random_args(args)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    if args.errorfilename is not None:
        hypercane.errors.errorstore.type = hypercane.errors.FileErrorStore(args.errorfilename)

    session = get_web_session(cache_storage=args.cache_storage)
    output_type = 'mementos'

    logger.info("Starting random sampling of URI-Ms.")

    urimdata = discover_resource_data_by_input_type(
        args.input_type, output_type, args.input_arguments, args.crawl_depth,
        session, discover_mementos_by_input_type
    )

    logger.info("Executing select true random algorithm")
    sampled_urims = select_true_random(list(urimdata.keys()), int(args.sample_count))

    logger.info("Writing sampled URI-Ms out to {}".format(args.output_filename))
    save_resource_data(args.output_filename, urimdata, 'original-resources', sampled_urims)

    logger.info("Done sampling.")

def print_usage():

    print("""hc sample is used execute different algorithms for selecting mementos from a web archive collection, document collection, a list of TimeMaps, or a directory containing WARCs

    Supported commands:
    * true-random - randomly chooses n URI-Ms from the input
    * dsa1 - select URI-Ms using the DSA1 (AlNoamany's) Algorithm
    * alnoamany - alias for dsa1
    * filtered-random - filters off-topic mementos, filters near-duplicates, and then samples k of the remainder, randomly

    Examples:

    hc sample true-random -i archiveit -a 8788 -o seed-output-file.txt -n 10 -cs mongodb://localhost/cache

    hc sample dsa1 -i timemaps -a timemaps.tsv -o dsa1-sample.tsv -cs mongodb://localhost/cache

""")

supported_commands = {
    "true-random": sample_with_true_random,
    "dsa1": sample_with_dsa1,
    "alnoamany": sample_with_dsa1,
    "filtered-random": sample_with_filtered_random
}

