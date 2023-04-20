#!/usr/bin/python3

from pathlib import Path
import extract_lib as ext
from datetime import datetime
from argparse import ArgumentParser

parser = ArgumentParser(description='Extract information from simulations in a given directory')
parser.add_argument('source', type=str, help='Source directory for simulations. Searched recursively.')
parser.add_argument('destination', type=str, help='Destination directory to put generated files.')
parser.add_argument('project', type=str, help='Project name used to tag generated files.')
parser.add_argument('--indicator', type=str, default='vasprun.xml', help='File to determine directories containing simulations and extract basic information.')
parser.add_argument('-f', '--force',  action='store_true', help='Force overwrite of existing files.')
parser.add_argument('--dryrun', action='store_true', help='Do not write any output.')

args = parser.parse_args()

force = args.force
creation_time = datetime.now().replace(microsecond=0).isoformat()
working_dir = 'Research/'
data_file = args.indicator
project_name = args.project
source_dir = args.source
destination_dir = args.destination
Path(destination_dir).mkdir(parents=True, exist_ok=True)

source_files = [v.resolve() for v in Path(source_dir).rglob(data_file)]

if len(source_files) < 1:
    raise(RuntimeError('Did not find any simulations'))

for source_file in source_files:
    # Get key and destination
    source_name = source_file.parts[-2]
    # source_name = str(source_file.parents[0])[-32:]
    destination_file = Path(destination_dir, source_name + '.md')

    # Create frontmatter
    frontmatter = f'---\naliases: [{source_name}]\ntags: [{project_name}]\ncreation: {creation_time}\n---\n\n'

    # Create location link string
    location_link = f'[Location on disk](file://{working_dir}{source_dir}{source_name})' + '\n\n'
    
    # Extract relevant strings
    root = ext.get_xml_root(str(source_file))
    body = ''
    body += ext.inline_value_string("Ions", ext.get_ions(root)) + '\n'
    body += ext.inline_value_string("Lattice", ext.get_lattices(root)) + '\n'
    body += ext.inline_value_string("Energy", ext.get_energies(root)) + '\n'

    # Create the files and write to them
    if destination_file.exists() and not(force):
        print(f'Skipping {destination_file}')
        continue

    if not(args.dryrun):
        with destination_file.open('w') as f:
            f.write(frontmatter)
            f.write(location_link)
            f.write(body)

    print(f'Created {destination_file}')

if args.dryrun:
    print('No changes made')
