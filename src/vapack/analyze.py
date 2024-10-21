from copy import deepcopy

import numpy as np
import numpy.typing as npt
import plotly.figure_factory as ff

import vapack.extensions as vext
from vapack.types import Ions, Poscar


def coordination_number(
    poscar: Poscar,
    index: list[int] | int,
    max_bondlength: float,
    species_filter: list[str] | None = None,
) -> int | npt.NDArray:
    poscar = deepcopy(poscar)
    poscar._convert_to_cartesian()
    species_filter = (
        list(poscar.species.keys()) if species_filter is None else species_filter
    )
    if not isinstance(index, (list,)):
        index = [index]
    coordinations = np.zeros(len(index), dtype=np.int64)
    for i, ion_i in enumerate(index):
        neighbors = vext.get_neighbors(poscar, ion_i, max_bondlength, "c", True)
        coordinations[i] = len(
            [i for i, ion in neighbors if ion.species in species_filter]
        )
    if len(coordinations) == 1:
        coordinations = coordinations[0]
    return coordinations


def all_species_coordination_number(
    poscar: Poscar,
    species: str,
    max_bondlength: float,
    species_filter: list[str] | None = None,
) -> int | npt.NDArray:
    ion_indices = [i for i, ion in poscar.ions if ion.species == species]
    return coordination_number(poscar, ion_indices, max_bondlength, species_filter)


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
    poscar = vext.get_centered_around(poscar, ion_center.position, poscar.mode)  # type: ignore
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
    chain: tuple[str, str, str] | str,
    max_bondlength: int,
    degrees: bool = False,
) -> npt.NDArray:
    poscar = deepcopy(poscar)
    # Interpret the chain argument
    if isinstance(chain, (tuple, list)):
        species_a = chain[0].strip()
        species_b = chain[2].strip()
        species_center = chain[1].strip()
    elif isinstance(chain, str):
        cl = chain.split("-")
        if len(cl) != 3:
            raise RuntimeError(f"Bad bond angle chain provided: {chain}")
        species_a = cl[0].strip()
        species_b = cl[2].strip()
        species_center = cl[1].strip()
    # Make sure the chain's species actually exist in the poscar
    for sp in (species_a, species_b, species_center):
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
        neighbors = vext.get_neighbors(
            poscar, i, max_bondlength, mode="c", periodic=True
        )
        # If not enough neighbors were discovered, then skip this one
        if len(neighbors) < 2:
            continue
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


def bond_angle_histogram_plotly(
    poscar: Poscar,
    chain: tuple[str, str, str] | str,
    max_bondlength: int,
    bin_width: float = 5,
    degrees: bool = False,
):
    # Set up graph information
    (amin, amax) = (0, 180) if degrees else (0, np.pi)
    units = "deg" if degrees else "rad"
    angles = all_bond_angles(poscar, chain, max_bondlength, degrees)
    if isinstance(chain, (list, tuple)):
        label = "-".join(chain)
    else:
        label = chain

    # Create kernel density estimation histogram using figure factory
    # This is "deprecated," but it's not because this functionality doesn't exist in Express
    # If this gets broken later, compute the kernel using scipy.stats.gaussian_kde and plot it
    # with a line graph on top of a basic histogram
    fig = ff.create_distplot(
        hist_data=angles, data_labels=label, bin_size=bin_width, show_rug=False
    )

    fig.layout.xaxis.title.text = f"Angle ({units})"
    fig.layout.yaxis.title.text = "p(x)"

    fig.update_xaxes(range=[amin, amax])

    return fig
