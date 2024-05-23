from vasptypes import Poscar, Ions
import numpy as np
from copy import deepcopy

def translate(ions:Ions, r=np.array(float)) -> Ions:
    """
    Translate the given selection along the x, y, or z dimension.
    """
    ions_t = deepcopy(ions)
    for i, _ in ions_t:
        ions_t[i].position += r
    return ions_t

def box_select(poscar:Poscar, x_range:list[float]=None, y_range:list[float]=None,\
               z_range:list[float]=None, mode:str=None) -> Ions:
    # If mode was not set, grab it automatically
    poscar_cp = deepcopy(poscar)
    mode = poscar_cp.mode if mode is None else mode

    # Convert the POSCAR to the correct mode if necessary
    converted = False
    if poscar_cp.mode[0].lower() != mode[0].lower():
        poscar_cp._toggle_mode()
        converted = True
    
    # Add ions that reside within box to selection list
    selection, indices = [], []
    for i, ion in poscar_cp.ions:
        if  ( x_range is None or (x_range[0] <= ion.position[0] <= x_range[1]) )\
        and ( y_range is None or (y_range[0] <= ion.position[1] <= y_range[1]) )\
        and ( z_range is None or (z_range[0] <= ion.position[2] <= z_range[1]) ):
            indices.append(i)
            selection.append(ion)

    # Reconvert the POSCAR if necessary
    if converted:
        poscar_cp._toggle_mode()
        
    return Ions(selection, indices)

def center_around(poscar:Poscar, index:int) -> Poscar:
    # Create a copy of the poscar
    poscar_cp = deepcopy(poscar)
    # Convert to direct if needed
    converted = False
    if poscar_cp.is_cartesian():
        poscar_cp._convert_to_direct()
        converted = True

    # Make sure everything is "inside" the cell
    poscar_cp._constrain()
    # If something is more than 0.5*lattice vector away,
    # either add or subtract to retrieve the appropriate image
    for i, ion in poscar_cp.ions:
        c = ion.position - poscar_cp.ions[index].position
        c = -1 * np.array(np.abs(c) > 0.5, dtype=int) * np.sign(c)
        poscar_cp.ions[i].position += c
    
    # Reconvert if needed
    if converted:
        poscar_cp._toggle_mode()
    
    return poscar_cp

def chain_select(poscar:Poscar, start_index:int, jump_distance:float=1.0,\
                 extent:int=np.inf, species_blacklist:list[str]=[],\
                 index_blacklist:list[int]=[], hydrogen_termination:bool=True):

    species_blacklist = [ s.lower() for s in species_blacklist ]

    # Initial quantities
    jump_distance2 = jump_distance**2
    selection = Ions([poscar.ions[start_index]], [start_index])
    jumps = [0]

    # From the selected ion, find neighbors in range
    first_hydrogen = True
    for i, selected_ion, jump in zip(selection, jumps):
        if jump >= extent:
            continue
        if hydrogen_termination \
        and not( first_hydrogen ) \
        and selected_ion.species == "H":
            continue
        poscar_cp = center_around(poscar, i)
        poscar_cp._convert_to_cartesian()
        poscar_cp_enum = poscar_cp.ions
        for j, ion in poscar_cp_enum:
            if j in selection.indices:
                continue
            if ion.species.lower() in species_blacklist:
                continue
            if j in index_blacklist:
                continue
            if ((poscar_cp.ions[i].position - poscar_cp.ions[j].position)**2).sum() > jump_distance2:
                continue
            
            # Append a copy of the original ion
            selection.append(poscar.ions[j])
            selection.indices.append(j)
            # Record how many jumps it took to get here
            jumps.append(jump+1)

        if first_hydrogen:
            first_hydrogen = False

    return selection