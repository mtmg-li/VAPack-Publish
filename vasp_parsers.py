from pathlib import Path
from ast import literal_eval
import numpy as np
from itertools import chain


def parse_incar(file:Path) -> tuple[dict, list]:
    """
    Return a dictionary of all key and value pairs from the given INCAR.
    """
    file = Path(file)
    incar_dict = {}
    comment_list = []

    with file.open('r') as incar_file:
        incar_text = incar_file.readlines()
        for line in incar_text:
            line = line.strip()
            # Line formatting sanity checks
            if len(line) == 0:
                continue
            if line[0] in ('#','!'):
                continue
            if not('=' in line):
                continue
            # Retrieve values without extra whitespace
            key, value = [i.strip() for i in line.split('=',maxsplit=1)]
            comment = ''
            # Determine if there are additional comments after the values
            if '!' in value or '#' in value:
                comment_start = np.array([value.find('!'), value.find('#')])
                comment_start *= -1 if -1 in comment_start else 1
                comment_start = np.abs( comment_start.min() )
                comment = value[comment_start+1:].strip()
                value = value[:comment_start].strip()
            # Make sure the key and value aren't blank
            if len(key) == 0 or len(value) == 0:
                continue
            # Evaluate the value string to cast as the appropriate type
            # Defaults to original string in event of failure
            try:
                value = literal_eval(value)
            except ValueError:
                pass
            except SyntaxError:
                pass
            # Modify the return dictionary and list
            incar_dict[str(key)] = value
            comment_list.append(comment)
    
    return incar_dict, comment_list


def parse_poscar(file:str) -> dict:
    """
    Return a dictionary of relevant information of the given POSCAR.
    """

    # Define paths and POSCAR dictionary
    file = Path(file)
    poscar_dict = {'comment': None,
            'scaling': None,
            'lattice_vectors': None,
            'species': None,
            'n_ions': None,
            'selective_dynamics': None,
            'position_mode' : None,
            'ion_position': None,
            'ion_selective_dynamics': None,
            'lattice_velocity': None,
            'ion_velocity': None,
            'mdextra': None}

    # Start reading the POSCAR file
    with file.open('r') as f:
        # Read comment line
        poscar_dict['comment'] = f.readline().strip()

        # Read scaling factor(s)
        scale = f.readline().strip().split()
        
        if len(scale) == 1:
            scale = scale*3
        elif len(scale) != 3:
            raise ValueError( 'Wrong number of scaling factors supplied in POSCAR!' )

        poscar_dict['scaling'] = np.asarray(scale, dtype=float)

        # Read lattice vectors
        lvl = []
        for _ in range(3):
            lv = np.asarray(f.readline().strip().split(), dtype=float)
            lvl.append(lv)
        poscar_dict['lattice'] = np.array(lvl, dtype=float).reshape((3,3))

        # Optional check, species names
        line = f.readline()
        if line.replace(' ', '').strip().isalpha():
            poscar_dict['species'] = line.split()
            # Line was optional, so advance to next
            line = f.readline()

        # Read ions per species
        poscar_dict['n_ions'] = [ int(n) for n in line.split() ]

        # Optional check, selective dynamics
        line = f.readline()
        if line[0].lower() == 's':
            poscar_dict['selective_dynamics'] = True
            poscar_dict['ion_selective_dynamics'] = []
            # Line was optional, so advance to next
            line = f.readline()

        # Read ion position mode
        if line[0].lower() in ('c','k'):
            poscar_dict['position_mode'] = 'Cartesian'
        if line[0].lower() == 'd':
            poscar_dict['position_mode'] = 'Direct'

        # Read ion positions
        poscar_dict['ion_position'] = []
        tions = np.sum(poscar_dict['n_ions'])
        for i in range(tions):
            line = f.readline().split()
            rv = np.array(line[0:3], dtype=float)
            poscar_dict['ion_position'].append(rv)
            
            # Read selective dynamics
            if poscar_dict['selective_dynamics']:
                sdl = line[3:6]
                # Check that these are actually selective dynamics markers
                if False in [ a in ['T', 'F'] for a in sdl ]:
                    raise ValueError( 'Unknown selective dynamics entry on atom {}'.format(i))
                poscar_dict['ion_selective_dynamics'].append(sdl)

        # TODO: Write code to read in lattice and ion velocities and MD extra

    return poscar_dict