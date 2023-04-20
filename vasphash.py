#!/usr/bin/python3

from hashlib import sha256
from datetime import datetime
from pathlib import Path
from argparse import ArgumentParser
from numpy import random as nprand
from sys import argv

# For a source, glob all simulation files by marker, then generate unique hashes for them all in the same directories

def arbitrary_hash():
    src_dir = 'Stage/test/'

    # Get time and random number to update hash
    time = datetime.now().replace(microsecond=0)
    rnum = nprand.randint(0,9999)

    # Make the hash
    h = sha256()
    h.update(f'{time}-{rnum}'.encode())
    h.digest()

    return h.hexdigest()


def execute(arguments:str):

    parser = ArgumentParser( description='Create an arbitrary SHA256 hash fragment to tag any detected VASP simulation directories recursively' )

    parser.add_argument( 'source', type=str, help='Source directory' )
    parser.add_argument( '-i', '--indicator', type=str, help='Pattern to match to detect a simulation directory', default='INCAR' )
    parser.add_argument( '-o', '--output', type=str, help='Name of output file with hash', default='tag' )
    parser.add_argument( '-l', '--length', type=int, help='Max length of resulting hash', default=16 )
    parser.add_argument( '-f', '--force', action='store_true', help='Force overwrite existing files' )
    parser.add_argument( '-d', '--dryrun', action='store_true', help='Do not write any files')

    args = parser.parse_args(arguments)

    src_dir = args.source
    ind_file = args.indicator
    dst_name = args.output
    maxlen = args.length
    force = args.force
    dryrun = args.dryrun

    sim_list = [ f for f in Path(src_dir).rglob(ind_file) ]

    for dir in sim_list:
        dst_file = Path( *dir.parts[:-1], dst_name )
        
        if dst_file.exists() and not(force):
            print( f'Skipping {dst_file}' )
            continue

        with dst_file.open('w') as f:
            dst_hash = arbitrary_hash()[:maxlen]
            if not(dryrun):
                f.write( dst_hash )
                print ( f'Wrote {dst_hash} to {dst_file}' )
            else:
                print( f'Would have written {dst_hash} to {dst_file}' )


if __name__ == '__main__':
    execute(argv[1:])