#!/usr/bin/python3

from pathlib import Path
import extract_lib as ext
from datetime import datetime
from argparse import ArgumentParser
from sys import argv


def execute(arguments):

    parser = ArgumentParser(description='Extract information from simulations in a given directory')

    parser.add_argument('source', type=str, help='Source directory for simulations. Searched recursively.')
    parser.add_argument('destination', type=str, help='Destination directory to put generated files.')
    parser.add_argument('project', type=str, help='Project name used to tag generated files.')
    parser.add_argument('-i','--indicator', type=str, default='vasprun.xml', help='Pattern to match to detect a simulation directory')
    parser.add_argument('-d','--data', type=str, default='vasprun.xml', help='Data file to pull from in each calculation directory')
    parser.add_argument('-t','--tag', type=str, default='tag.txt', help='The file containing the hash for tagging')
    parser.add_argument('--force',  action='store_true', help='Force overwrite of existing files.')
    parser.add_argument('--dryrun', action='store_true', help='Do not write any output.')

    args = parser.parse_args(arguments)

    # Set the variables
    data_file = args.data
    tag_file = args.tag
    indicator_file = args.indicator
    source_dir = args.source
    destination_pd = args.destination
    project_name = args.project
    force = args.force
    dryrun = args.dryrun

    # Get the current time
    creation_time = datetime.now().replace(microsecond=0).isoformat()

    # Make the destination parent folder
    if not(dryrun):
        Path(destination_pd).mkdir(parents=True, exist_ok=True)

    # Recursively search through the source for all calculation folders
    source_files = [v.resolve() for v in Path(source_dir).rglob(indicator_file)]

    # Quit with message if nothing found
    if len(source_files) < 1:
        raise(RuntimeError('Did not find any simulations'))

    # For each calculation folder
    for source_file in source_files:
        # Get the calculation folder
        calc_dir = Path(*source_file.parts[:-1])

        # Get the tag to name the new dir
        src_tag = ''
        src_tag_file = Path(calc_dir, tag_file)

        if not(src_tag_file.exists()):
            print( f'Could not find {src_tag_file}' )
            continue

        with src_tag_file.open('r') as f:
            src_tag = f.read().strip()

        # Make sure there's actually something in src_tag
        if len(src_tag) < 1:
            raise(RuntimeError(f'Tag file {src_tag_file} empty'))

        # Create the destination directory
        dst_calc_dir = Path(destination_pd, src_tag)
        if not(dryrun):
            dst_calc_dir.mkdir(parents=True, exist_ok=True)
        
        # Create frontmatter
        frontmatter = f'---\naliases: [{src_tag}]\ntags: [{project_name}]\ncreation: {creation_time}\n---\n\n'

        # Get the source for (meta)data
        calc_data_file = Path(calc_dir, data_file)
        
        # If the source exists, extract the metadata to body, else leave blank
        body = ''
        if calc_data_file.exists():
            try:
                root = ext.get_xml_root(str(calc_data_file))
                body += ext.inline_value_string("Ions", ext.get_ions(root)) + '\n'
                body += ext.inline_value_string("Lattice", ext.get_lattices(root)) + '\n'
                body += ext.inline_value_string("Energy", ext.get_energies(root)) + '\n'
            except ext.ET.ParseError:
                body = '> [!Error] Failed to Parse'
                print(f'!!! Failed to read {calc_data_file}. Skipping !!!')
        else:
            body = '> [!Warning] No data at extraction time'
            print(f'Skipping extraction of {calc_data_file}')

        # Create the file and write to it
        dst_data_file = Path(dst_calc_dir, src_tag + '.md')
        if dst_data_file.exists() and not(force):
            print(f'Skipping {dst_data_file}')
            continue

        # Write to the file if it's not a dryrun
        if not(dryrun):
            with dst_data_file.open('w') as f:
                f.write(frontmatter)
                f.write(body)
                print(f'Wrote to {dst_data_file}')
        else:
            print(f'Would have written to {dst_data_file}')


if __name__ == "__main__":
    execute(argv[1:])
