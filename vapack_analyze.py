from copy import deepcopy

import numpy as np
import numpy.typing as npt

import vasptypes_extension as vte
from vasptypes import Ions, Poscar


def bond_angle(
    poscar: Poscar, indices: tuple[int, int, int], degrees: bool = False
) -> float:
    """
    Given any three atoms/ions, return the angle formed between them.
    Assume the second given atom/ion, center_ion, is the angle point.
    """
    # Convert the poscar to cartesian since bond angle
    # makes little sense in direct coordinates
    poscar = deepcopy(poscar)
    poscar._convert_to_cartesian()
    # Center the poscar around the central ion/atom
    ion_center = poscar.ions[indices[1]]
    poscar = vte.get_centered_around(poscar, ion_center.position, poscar.mode) # type: ignore
    # Create some better names
    ion_a = poscar.ions[indices[0]]
    ion_b = poscar.ions[indices[2]]
    # Unit vector from center to a
    ra = ion_a.position - ion_center.position
    ra = ra / np.sqrt((ra**2).sum())
    # Unit vector from center to b
    rb = ion_b.position - ion_center.position
    rb = rb / np.sqrt((rb**2).sum())
    # Basic trig to get the (acute) angle
    cross = np.cross(ra, rb)
    mag = np.sqrt((cross**2).sum())
    theta = np.arcsin(mag)
    # Use vector projection to recover obtuse vs acute angle info
    dot = np.dot(ra, rb)
    # Do nothing if the angle is acute
    if dot >= 0:
        pass
    # Or set it to the difference from pi to the (wrong) theta if obtuse
    else:
        theta = np.pi - theta
    # Convert to degrees if requested
    if degrees:
        theta *= 180 / np.pi
    # and return
    return theta


def all_bond_angles(
    poscar: Poscar,
    chain: tuple[str, str, str],
    max_bondlength: int,
    degrees: bool = False,
) -> npt.NDArray:
    # Make sure the chain's species actually exist in the poscar
    poscar = deepcopy(poscar)
    species_a = chain[0]
    species_b = chain[2]
    species_center = chain[1]
    for sp in chain:
        if sp not in list(poscar.species.keys()):
            raise RuntimeError(
                f'Could not find species {sp} in provided poscar "{poscar.comment}"'
            )
    # Create a list of all chains that can be found within the poscar by doing a radial neighbor search
    # around the central atom/ion
    triplet_list = []
    # TODO: Fix this! An empty declaration populates with data???
    center_ions = Ions([], [])
    for i, ion in poscar.ions:
        if ion.species == species_center:
            center_ions.append(ion, i)
    for i, ion_c in center_ions:
        neighbors = vte.get_neighbors(
            poscar, i, max_bondlength, mode="c", periodic=True
        )
        # Wretched complex and c-style loop
        for j, (jj, ion_a) in enumerate(neighbors):  # type: ignore
            if j == len(neighbors):
                break
            for k, (kk, ion_b) in enumerate(neighbors):  # type: ignore
                if k <= j:
                    continue
                if ion_a.species != species_a or ion_b.species != species_b:
                    continue
                triplet_list.append(Ions([ion_a, ion_c, ion_b], [jj, i, kk]))
    bond_angles = np.zeros(len(triplet_list), dtype=float)
    for i, triplet in enumerate(triplet_list):
        bond_angles[i] = bond_angle(poscar, triplet.indices, degrees)
    return bond_angles


def bond_angle_histogram(
    poscar: Poscar,
    chain: tuple[str, str, str],
    max_bondlength: int,
    bins: int = 10,
    degrees: bool = False,
):
    (amin, amax) = (0, 180) if degrees else (0, np.pi)
    angles = all_bond_angles(poscar, chain, max_bondlength, degrees)
    return np.histogram(angles, bins, range=(amin, amax))
