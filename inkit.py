#!/usr/bin/env python3

from sys import argv
from argparse import ArgumentParser
from pathlib import Path
from yaml import load, CLoader


TAB_SIZE = 4
KEY_WIDTH = 3*TAB_SIZE
VAL_WIDTH = 3*TAB_SIZE


def incar_system_line(incar_dict:dict, system_str:str):
    '''
    Return a copy of the INCAR dictionary with the system tag reformated to the given string
    '''
    try:
        incar_dict.pop('System')
    except KeyError:
        pass
    temp_dict = {'System': [{'tag':'System', 'value':system_str, 'comment':''}]}
    temp_dict.update(incar_dict)
    return temp_dict


def format_incar_line(line_dict:dict) -> str:
    '''
    Format a dictionary of tag, value, and comment as a line in an INCAR file
    '''
    if len(line_dict['comment']) > 0:
        line_str = '{0:<{key_width}} = {1:<{val_width}} ! {2}'.format(*line_dict.values(), key_width=KEY_WIDTH-1, val_width=VAL_WIDTH-3)
    else:
        line_str = '{0:<{key_width}} = {1:<{val_width}}'.format(*line_dict.values(), key_width=KEY_WIDTH-1, val_width=VAL_WIDTH-2)
    return line_str


def format_incar_section(section_key:str, tags:list) -> str:
    '''
    Format a list of tags as a section of an INCAR file
    '''
    section_string = '# ' + section_key.capitalize() + '\n\n'
    if type(tags) in [list, tuple]:
        for tag in tags:
            section_string += format_incar_line(tag) + '\n'
    return section_string.strip()


def format_incar(incar_dict:dict) -> str:
    '''
    Format the given dictionary as a complete INCAR file
    '''
    section_strings = [ format_incar_section(section, tag) for section, tag in incar_dict.items() ]
    return '\n\n'.join(section_strings)


def update_incar_tag(incar_dict:dict, new_tag:dict, section='Unspecified'):
    '''
    Update the INCAR dictionary with the given new tag (and section)
    '''
    # First replace any existing occurences, ignoring the section parameter
    for section_key, section_value in incar_dict.items():
        if not( type(section_value) in [tuple, list] ):
            continue
        for tag in section_value:
            if tag['tag'] == new_tag['tag']:
                tag['value'] = new_tag['value']
                tag['comment'] = new_tag['comment']
                return
    
    # If the tag isn't preexisting, search for the correct section to add the tag
    for section_key in incar_dict.keys():
        if section_key.lower() == section.lower():
            # If section is empty, initialize it as a list
            if incar_dict[section_key] is None:
                incar_dict[section_key] = []
            incar_dict[section_key].append(new_tag)
            return
    
    # If neither tag nor section exist, create them both
    incar_dict.update({section.lower().capitalize(): [new_tag]})


def update_incar_dict(incar_dict:dict, new_dict:dict):
    '''
    Update the INCAR dict with information in the new dict
    '''
    for section, tags in new_dict.items():
        if tags == None:
            continue
        for tag in tags:
            update_incar_tag(incar_dict, tag, section)


def execute(arguments):
    parser = ArgumentParser(description='Create an INCAR file from provided templates')

    parser.add_argument('source', nargs='+', type=str, help='Source files for INCAR templates')
    parser.add_argument('-o','--output', type=str, default='INCAR', help='Output file directory and name')
    parser.add_argument('-d', '--templatedir', type=str, default='templates/yaml', help='Template directory')
    parser.add_argument('-s', '--system', type=str, help='System name')

    args = parser.parse_args(arguments)

    template_dir = Path(args.templatedir)
    # Create paths to the files, adding the .yaml suffix if it is not specified manually
    template_files = [ Path(template_dir, i + '.yaml'*(i.find('.yaml')<0)) for i in args.source ]
    
    data = None
    for template in template_files:
        with template.open('r') as f:
            template_str = f.read()
            if data == None:
                data = load(template_str, Loader=CLoader)
            else:
                new_data = load(template_str, Loader=CLoader)
                update_incar_dict(data, new_data)
    
    if not( args.system == None ):
        data = incar_system_line(data, args.system)

    incar_file = Path(args.output)

    incar_str = format_incar(data)
    with incar_file.open('w') as f:
        f.write(incar_str)


if __name__ == "__main__":
    execute(argv[1:])
