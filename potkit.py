from sys import argv
from pathlib import Path
import poskit_lib as pkl
from argparse import ArgumentParser

def potcar(args):

    # Initialize species list
    species = []

    # If the POSCAR is none, then use the provided list
    if args.poscar.lower() == 'none':
        species = args.list
    
    # If the POSCAR is a file (not 'none')
    else:
        poscar = pkl.Base.read_poscar(args.poscar)
        species = poscar['species']

    # Verbose species message
    if args.verbose:
        if args.poscar.lower() != 'none':
            print( 'Creating a POTCAR from {}'.format(args.poscar) )
        print( 'Using species/potentials {}'.format(species) )

    # Verbose potential approximation method message
    directory = Path(args.directory)
    if args.verbose:
        if directory.name.lower() in ['pbe', 'lda']:
            print( 'Using {} potentials'.format(directory.name.upper()) )
        elif len(species) > 1:
            print( 'Using PBE potentials' )
        else:
            print( 'Using LDA potentials' )

    # Generate and write the potcar
    if not(args.nowrite):
        pkl.Base.write_potcar( species, args.directory, args.output )

        if args.verbose:
            print( 'Changes written to {}'.format(args.output) )

    # Or don't...
    else:
        if args.verbose:
            print( 'No changes written' )
        pass

def execute(arguments):

    # Define potcar command
    parser = ArgumentParser( 'potcar', help='Create a potcar from given input' )
    parser.add_argument( 'poscar', type=str, help='Source POSCAR for creating the list of species/potentials for the POTCAR | May also specify \'none\' to instead use the list argument alone' )
    parser.add_argument( '-o', '--output', type=str, default='POTCAR', help='Output file <DEFAULT POTCAR>' )
    parser.add_argument( '-l', '--list', nargs='+', help='List of potentials | Useful for potentials that differ from the ion species name')
    parser.add_argument( '-d', '--directory', default='./potcar', type=str, help='Directory of POTCAR folders <DEFAULT ./potcar/> | Can be used to specify PBE or LDA manually' )

    args = parser.parse_args(arguments)



if __name__ == "__main__":
    execute(argv[1:])