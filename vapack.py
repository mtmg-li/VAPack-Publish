#!/usr/bin/env python3

"""
Command line program that provides easy access to tools in Vasp Tool Kit
"""

import vapack_lib
from argparse import ArgumentParser
from copy import deepcopy
import sys

subcommands = [ sc for sc in vapack_lib.Subcommand.__subclasses__() ]

# Define top level parser
parser = ArgumentParser( description='Do things for VASP' )
parser.add_argument( '-v', '--verbose', action='store_true' )
parser.add_argument( '-n', '--no_write', action='store_true' )
subparsers = parser.add_subparsers()

# Iterate through the subcommands and add the subparsers to the top level
for subcommand in subcommands:
    subcommand.parser.set_defaults( func=subcommand.run )
    subparsers.add_parser(subcommand.__name__, parents=[subcommand.parser],
                          add_help=False, help=subcommand.description)

# Run this stuff
args = parser.parse_args()

# If a subparser was called, it'll set func in the args namespace
if args.__contains__('func'):
    # Get a dictionary of the arguments to pass to the run function
    arg_dict = deepcopy(args.__dict__)
    # Remove the func entry
    arg_dict.pop('func')
    # Run the appropriate function with all arguments
    args.func(**arg_dict)

# If func was not set, print the help message and quit
else:
    parser.print_help(sys.stderr)
    sys.exit(1)