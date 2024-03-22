from pathlib import Path
from ast import literal_eval
import numpy as np

def parse_incar(file:str, evaluate=False) -> dict:
    """
    Return a dictionary of all key and value pairs from the given INCAR.
    """
    file = Path(file)
    incar_dict = {}
    
    with file.open('r') as f:
        lines = f.readlines()
        
        for line, linenumber in zip(lines, range(1,len(lines)+1)):
            try:
                line = line.strip()
                # Skip comment lines
                if line[0] in ('#','!'):
                    continue
                
                # Find the split at the = character
                key_end = line.find('=')
                if key_end < 0:
                    raise RuntimeError

                # Retrieve the key
                key = line[0:key_end].strip()
                # Check key exists
                if len(key) < 1:
                    raise RuntimeError
                # Make sure there are no spaces
                if len(key.split()) > 1:
                    raise RuntimeError
                
                # Retrieve the value and skip trailing comments
                value_end = max( [line.find('#'), line.find('!')] )
                if value_end == -1:
                    value_end = len(line)+1
                value = line[key_end+1:value_end].strip()
                # Check value exists
                if len(value) < 1:
                    raise RuntimeError
                # Determine types and lists, if applicable
                if evaluate:
                    value = value.split()    
                    for i in range(len(value)):
                        try:
                            value[i] = literal_eval(value[i])
                        except SyntaxError:
                            pass
                    if len(value) == 1:
                        value = value[0]
                
                incar_dict[key] = value
                
            except RuntimeError:
                raise RuntimeError('line {}: {}'.format(linenumber, line))
            
    return incar_dict


def parse_poscar(file:str) -> dict:
    """
    Return a dictionary of relevant information of the given POSCAR.
    """

    # Define paths and POSCAR dictionary
    file = Path(file)
    poscar_dict = {'comment': None,
            'scaling': None,
            'lattice': None,
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