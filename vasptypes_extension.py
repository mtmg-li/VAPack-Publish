from vasptypes import Poscar, Ions
import numpy as np

def box_select(poscar:Poscar, x_range:list[float]=None, y_range:list[float]=None,\
               z_range:list[float]=None, mode:str=None) -> Ions:
    # If mode was not set, grab it automatically
    mode = poscar.mode if mode is None else mode

    # Convert the POSCAR to the correct mode if necessary
    converted = False
    if poscar.mode[0].lower() != mode[0].lower():
        poscar._toggle_mode()
        converted = True
    
    # Add ions that reside within box to selection list
    selection, indices = [], []
    for i, ion in enumerate(poscar.ions):
        if  ( x_range is None or (x_range[0] <= ion.position[0] <= x_range[1]) )\
        and ( y_range is None or (y_range[0] <= ion.position[1] <= y_range[1]) )\
        and ( z_range is None or (z_range[0] <= ion.position[2] <= z_range[1]) ):
            indices.append(i)
            selection.append(ion)

    # Reconvert the POSCAR if necessary
    if converted:
        poscar._toggle_mode()
        
    return Ions(selection, indices)

def chain_select(poscar:Poscar, starting_ion_index:int, jump_distance:float=1.0,\
                 extent:int=None, whitelist:list[str]=None, blacklist:list[str]=None,\
                 hydrogen_termination:bool=True):
    pass