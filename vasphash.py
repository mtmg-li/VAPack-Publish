#!/usr/bin/python3

from hashlib import md5
from pathlib import Path
from argparse import ArgumentParser

# Return a md5 hash from a list of files and their contents
def hash_files(files:list):
    if not(type(files) in [list, tuple]):
        files = [files]
    m = md5()
    for file in files:
        file = Path(file)
        with file.open('r') as f:
            m.update(file.name.encode())
            m.update(f.read().encode())
    m.digest()
    return m.hexdigest()

# Create parser and arguments
parser = ArgumentParser( description='Return MD5 hash of files' )
parser.add_argument( 'files', type=str, nargs='+', help='List of files to generate hash from' )
args = parser.parse_args()

# Parse command and print MD5 hash
print( hash_files( args.files ) )
