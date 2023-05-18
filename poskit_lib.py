"""
Module containing methods and tools to create, format, and analyze input and output files for the Vienna Ab-initio Simulation Package.
"""

from pathlib import Path
import numpy as np
from copy import deepcopy

class Base:
    """
    Supporting methods for the vasp toolkit. These rely only on built-ins and common third-party packages.
    """


    def read_poscar ( file:str ) -> dict:
        """
        Creates a dictionary containing all attributes from a given POSCAR file
        Keys: comment, scaling, lattice, species, nions, sdynam, rmode, rions, sdions, latvel, ionvel, mdextra
        """

        # Define paths and POSCAR dictionary
        POSCAR = Path(file)
        dictPOSCAR = {'comment': None,
                'scaling': None,
                'lattice': None,
                'species': None,
                'nions':   None,
                'sdynam':  None,
                'rmode' :  None,
                'rions':   None,
                'sdions':  None,
                'latvel':  None,
                'ionvel':  None,
                'mdextra': None}

        # Start reading the POSCAR file
        with POSCAR.open('r') as f:
            # Read comment line
            dictPOSCAR['comment'] = f.readline().strip()

            # Read scaling factor(s)
            scale = f.readline().strip().split()
            
            if len(scale) == 1:
                scale = scale*3
            elif len(scale) != 3:
                raise ValueError( 'Wrong number of scaling factors supplied in POSCAR!' )

            dictPOSCAR['scaling'] = np.asarray(scale, dtype=float)

            # Read lattice vectors
            lvl = []
            for _ in range(3):
                lv = np.asarray(f.readline().strip().split(), dtype=float)
                lvl.append(lv)
            dictPOSCAR['lattice'] = np.array(lvl, dtype=float).reshape((3,3))

            # Optional check, species names
            line = f.readline()
            if line.replace(' ', '').strip().isalpha():
                dictPOSCAR['species'] = line.split()
                # Line was optional, so advance to next
                line = f.readline()

            # Read ions per species
            dictPOSCAR['nions'] = [ int(n) for n in line.split() ]

            # Optional check, selective dynamics
            line = f.readline()
            if line[0].lower() == 's':
                dictPOSCAR['sdynam'] = True
                dictPOSCAR['sdions'] = []
                # Line was optional, so advance to next
                line = f.readline()

            # Read ion position mode
            if line[0].lower() in ('c','k'):
                dictPOSCAR['rmode'] = 'Cartesian'
            if line[0].lower() == 'd':
                dictPOSCAR['rmode'] = 'Direct'

            # Read ion positions
            dictPOSCAR['rions'] = []
            tions = np.sum(dictPOSCAR['nions'])
            for i in range(tions):
                line = f.readline().split()
                rv = np.array(line[0:3], dtype=float)
                dictPOSCAR['rions'].append(rv)
                
                # Read selective dynamics
                if dictPOSCAR['sdynam']:
                    sdl = line[3:6]
                    # Check that these are actually selective dynamics markers
                    if False in [ a in ['T', 'F'] for a in sdl ]:
                        raise ValueError( 'Unknown selective dynamics entry on atom {}'.format(i))
                    dictPOSCAR['sdions'].append(sdl)

            # TODO: Write code to read in lattice and ion velocities and MD extra

            return dictPOSCAR


    def gen_poscar ( poscar:dict ) -> str:
        """
        Return a formatted string of the POSCAR dictionary as would be found in a file.
        """

        poscarString = ''

        # Write comment line
        poscarString += poscar['comment']
        poscarString += '\n'
        
        # Write scaling factor
        if len(poscar['scaling']) > 1 and poscar['scaling'].sum() != poscar['scaling'][0]*3:
            poscarString +=  '  {:>11.8f}  {:>11.8f}  {:>11.8f}'.format(*poscar['scaling'])
            poscarString += '\n'
        else:
            poscarString +=  '  {:>11.8f}'.format(poscar['scaling'][0])
            poscarString += '\n'

        # Write lattice vectors
        for i in poscar['lattice']:
            poscarString +=  '    {:>11.8f}  {:>11.8f}  {:>11.8f}'.format(*i)
            poscarString += '\n'

        # Write the species names
        line = ''
        for species in poscar['species']:
            line += '{:>4s} '.format(species)
        poscarString +=  '  ' + line.rstrip()
        poscarString += '\n'

        # Write species numbers
        line = ''
        for n in poscar['nions']:
            line += '{:>4d} '.format(n)
        poscarString +=  '  ' + line.rstrip()
        poscarString += '\n'

        # Write selective dynamics if enabled
        if poscar['sdynam'] == True:
            poscarString += 'Selective dynamics'
            poscarString += '\n'

        # Write position mode
        poscarString += poscar['rmode']
        poscarString += '\n'

        # Write the ion positions with selective dynamics tags
        line = ''
        for i in range(len(poscar['rions'])):
            line = '{:>11.8f}  {:>11.8f}  {:>11.8f}'.format(*poscar['rions'][i])
            if poscar['sdynam'] == True:
                line += ' {:>1s} {:>1s} {:>1s}'.format(*poscar['sdions'][i])
            poscarString +=  '  ' + line.rstrip()
            poscarString += '\n'

    # TODO: Write code to write lattice vector and ion velocities and MD extra

        return poscarString


    def write_poscar ( poscar:dict, file:str ) -> str:
        """
        Write the POSCAR dictionary to the given file.
        Returns a copy of the generated POSCAR.
        """

        # Define file names and paths
        file = Path(file)

        # Get the POSCAR string
        poscarString = Base.gen_poscar(poscar)

        # Write the POSCAR file
        with file.open('w') as f:
            f.write(poscarString)


    def gen_potcar ( species:list, potcarDir:str ) -> str:
        """
        From a list of species, generate a POTCAR from the POTCAR directory.
        """

        # Define file names and paths
        potcarDir = Path(potcarDir)

        # Choose the LDA or PBE automatically if it isn't specified
        if not(potcarDir.name.lower() in ['pbe', 'lda']):
            if len(species) > 1:
                potcarDir = Path(potcarDir, 'PBE')
            else:
                potcarDir = Path(potcarDir, 'LDA')

        # Create a list of paths for the species' POTCARs
        speciesPath = [ Path(potcarDir, sp, 'POTCAR') for sp in species ]

        # Return the POTCARs as one concatenated string
        potcar = ''
        for sp in speciesPath:
            potcar += sp.read_text()
        
        return potcar
    
    
    def write_potcar ( species:list, potcarDir:str, file:str ) -> str:
        """
        From a list of species, generate a POTCAR and write it to the output file.
        Returns a copy of the generated POTCAR.
        """
        
        # Define file names and paths
        file = Path(file)

        # Get the POTCAR string
        potcar = Base.gen_potcar(species, potcarDir)

        # Write the POTCAR file and return a copy of the POTCAR
        with file.open('w') as f:
            f.write(potcar)

        return potcar


    def add_vacuum ( poscar:dict, vacuumDepth:list) -> dict:
        """
        Return a copy of the POSCAR with vacuum added in the specified dimensions.
        """

        # Create a copy of poscar to modify
        poscar = deepcopy(poscar)

        # If the POSCAR is Direct, convert to Cartesian to work with it
        converted = False
        if poscar['rmode'] == 'Direct':
            poscar = Base.convert_cartesian(poscar)
            converted = True

        elif not( poscar['rmode'] in ['Cartesian', 'Direct'] ):
            raise( ValueError('Unrecognized coordinate mode. Aborting.') )
        
        scale = poscar['scaling']
        # Add the vacuum in the direction of the lattice vectors
        for i in range(3):
            row = poscar['lattice'][i]
            uv = row/np.sqrt(np.sum(row**2))
            row += vacuumDepth[i] * uv / scale[i]

        # Return POSCAR to original position mode
        if converted:
            poscar = Base.convert_direct(poscar)

        return poscar


    def convert_direct ( poscar:dict ) -> dict:
        """
        Return a copy of the POSCAR converted from Cartesian to Direct
        """

        # Create a copy of the POSCAR
        poscar = deepcopy(poscar)

        # Create the transformation matrix
        A = poscar['lattice'].transpose()
        Ainv = np.linalg.inv(A)

        # Convert all ion positions to fractions of the lattice vectors and round to zero
        delta = 1e-8
        for r,i in zip( poscar['rions'], range(len(poscar['rions'])) ):
            r = Ainv @ r
            r = r * np.array(r>delta, dtype=int)
            poscar['rions'][i] = r

        # Change the rmode to Direct
        poscar['rmode'] = 'Direct'
        
        return poscar


    def convert_cartesian ( poscar:dict ) -> dict:
        """
        Return a copy of the POSCAR converted from Direct to Cartesian
        """

        # Create a copy of the POSCAR
        poscar = deepcopy(poscar)

        # Create the transformation matrix
        A = poscar['lattice'].transpose()

        # Multiple each ion position by the transformation matrix and round to zero
        delta = 1e-8
        for r,i in zip( poscar['rions'], range(len(poscar['rions'])) ):
            r = A @ r
            r = r * np.array(r>delta, dtype=int)
            poscar['rions'][i] = r

        # Change the rmode to Cartesian
        poscar['rmode'] = 'Cartesian'

        return poscar


    def convert_toggle ( poscar:dict ) -> dict:
        """
        Return a copy of the poscar in the opposite position mode
        """

        poscar = deepcopy(poscar)

        if poscar['rmode'] == 'Cartesian':
            poscar = Base.convert_direct(poscar)
        elif poscar['rmode'] == 'Direct':
            poscar = Base.convert_cartesian(poscar)
        else:
            raise ValueError( 'Unrecognized position mode' )
        
        return poscar


    def sd_box ( poscar:dict, begin:np.array, end:np.array, sddeg:list ) -> dict:
        """
        Define a 3D box, direct or in cartesian, and apply the chosen selective dynamics flags to all atoms within.
        Returns a copy of the modified potcar dictionary.
        """

        # Create a copy of the poscar to work on
        poscar = deepcopy(poscar)

        # If sdynamics is already enabled, iterate in such a way as to not erase values for ions that don't meet criteria
        if poscar['sdynam']:

            # Create a new list of the associated selective dynamic degrees for eachion
            sdionsNew = []

            # For each ion inside the box apply the changed degrees, otherwise keep the original
            for r, sd in zip( poscar['rions'], poscar['sdions'] ):
                if np.sum( np.array( [r >= begin, r <= end], dtype=int ) ) == 6:
                    sdionsNew.append( sddeg )
                else:
                    sdionsNew.append( sd )
            poscar['sdions'] = sdionsNew

        # If sdynamics is not enabled, enable it and allow full freedom for any ion that doesn't meet criteria
        else:
            poscar['sdynam'] = True
            poscar['sdions'] = []

            # For each ion inside the box apply the changed degrees, otherwise allow full freedoms
            for ion in poscar['rions']:
                if np.sum( np.array(ion >= begin, dtype=int) ) == 3 and np.sum( np.array(ion <= end, dtype=int) ) == 3:
                    poscar['sdions'].append(sddeg)
                else:
                    poscar['sdions'].append( ['T', 'T', 'T'] )

        return poscar

    
    # Translate atoms distance along given direction
    def translate ( poscar:dict ) -> dict:
        pass


    # Rotate atoms around axis
    def rotate ( poscar:dict ) -> dict:
        pass