from copy import deepcopy

import numpy as np
import numpy.typing as npt

from vapack.types import Ion, Ions, Poscar  # type: ignore


def translate(ions: Ions, r: npt.NDArray[np.float64]) -> Ions:
    """
    Translate the given selection along the x, y, or z dimension.
    """
    ions_t = deepcopy(ions)
    r = np.array(r)
    for i, _ in enumerate(ions_t):
        ions_t[i].position += r
    return ions_t


def get_neighbors(
    poscar: Poscar,
    index: int,
    radius: float,
    mode: str | None = None,
    periodic: bool = True,
) -> Ions:
    """
    Return a list of all ions that lie within a sphere around the ion identified by index.
    """

    poscar = deepcopy(poscar)
    mode = poscar.mode if mode is None else mode
    converted = False
    if mode[0].lower() != poscar.mode[0].lower():
        converted = True
        poscar._toggle_mode()

    # TODO: Type hinting with 'center'
    center = poscar.ions[index].position
    selection = get_select_sphere(poscar, center, radius, mode, periodic)  # type: ignore
    # Remove the focused ion from the neighbors list
    # This is used since the Ions object does not support "popping" by poscar index
    # (at the time of writing)
    for i, (_, ion) in enumerate(selection):  # type: ignore
        if np.allclose(ion.position, center, rtol=0.01):
            selection.pop(i)

    # If the original POSCAR was converted, undo that conversion on the list
    if converted and poscar.is_cartesian():
        # Reverting from cartesian to direct
        A = poscar.lattice.transpose()
        Ainv = np.linalg.inv(A)
        for i, (_, ion) in enumerate(selection):  # type: ignore
            selection[i]._apply_transformation(Ainv)
    elif converted and poscar.is_direct():
        # Reverting from direct to cartesian
        A = poscar.lattice.transpose()
        for i, (_, ion) in enumerate(selection):  # type: ignore
            selection[i]._apply_transformation(A)

    return selection


def get_select_sphere(
    poscar: Poscar,
    center: npt.NDArray[np.float64],
    radius: float,
    mode: str | None = None,
    periodic: bool = True,
) -> Ions:
    """
    Return a list of all the ions that fall within a sphere centered at any point in the cell.
    If used in direct coordinates, the sphere gets distorted with the shape of the lattice.
    Make of that what you will.
    """
    poscar = deepcopy(poscar)
    center = np.array(center)

    # Check the mode and convert if needed
    mode = poscar.mode if mode is None else mode
    converted = False
    if poscar.mode[0].lower() != mode[0].lower():
        poscar._toggle_mode()
        converted = True

    # If periodic, center the cell around the point
    if periodic:
        poscar = get_centered_around(poscar, center, mode)

    # Iterate through each ion in the poscar and check the distance from the center
    # Populate an Ions list with all that reside within
    selection_temp: list[tuple[Ion, int]] = []
    for i, ion in poscar.ions:
        d = np.sqrt(((ion.position - center) ** 2).sum())
        if d <= radius:
            selection_temp.append((ion, i))
    selection = Ions([i[0] for i in selection_temp], [i[1] for i in selection_temp])

    # If the poscar was converted, reconvert the ions positions
    # Case of converting from cartesian to direct
    if converted and poscar.mode == "Cartesian":
        A = poscar.lattice.transpose()
        Ainv = np.linalg.inv(A)
        for i, _ in enumerate(selection):
            selection[i]._apply_transformation(Ainv)
    # Case of converting from direct to cartesian
    elif converted and poscar.mode == "Direct":
        A = poscar.lattice.transpose()
        for i, _ in enumerate(selection):
            selection[i]._apply_transformation(A)
    return selection


def get_select_box(
    poscar: Poscar,
    x_range: list[float] | None = None,
    y_range: list[float] | None = None,
    z_range: list[float] | None = None,
    mode: str | None = None,
) -> Ions:
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
        if (
            (x_range is None or (x_range[0] <= ion.position[0] <= x_range[1]))
            and (y_range is None or (y_range[0] <= ion.position[1] <= y_range[1]))
            and (z_range is None or (z_range[0] <= ion.position[2] <= z_range[1]))
        ):
            indices.append(i)
            selection.append(ion)

    # Reconvert the POSCAR if necessary
    if converted:
        poscar_cp._toggle_mode()

    return Ions(selection, indices)


def get_centered_around(
    poscar: Poscar, point: npt.NDArray[np.float64], mode: str = "Direct"
) -> Poscar:
    # Create a copy of the poscar
    poscar_cp = deepcopy(poscar)
    # Convert to direct if needed. It's far easier to work in direct here.
    converted = False
    if poscar_cp.is_cartesian():
        poscar_cp._convert_to_direct()
        converted = True
    # Make sure the point is a numpy array for math
    if type(point) is not npt.NDArray:
        point = np.array(point)
    if np.size(point) != 3:
        raise RuntimeError(
            f"Centering around point {point} is ambiguous without 3 dimensions"
        )
    # If asked to work in a cartesian, convert the point to direct
    if mode[0].lower() == "c":
        A = poscar.lattice.transpose()
        Ainv = np.linalg.inv(A)
        point = Ainv @ point

    # Make sure everything is "inside" the cell
    poscar_cp._constrain()
    # If something is more than 0.5*lattice vector away,
    # either add or subtract to retrieve the appropriate image
    for i, ion in poscar_cp.ions:
        c = ion.position - point
        c = -1 * np.array(np.abs(c) > 0.5, dtype=int) * np.sign(c)
        poscar_cp.ions[i].position += c

    # Reconvert if needed
    if converted:
        poscar_cp._toggle_mode()

    return poscar_cp


def get_select_chain(
    poscar: Poscar,
    start_index: int,
    jump_distance: float = 1.0,
    extent: int | float = np.inf,
    species_blacklist: list[str] = [],
    index_blacklist: list[int] = [],
    hydrogen_termination: bool = True,
) -> Ions:
    species_blacklist = [s.lower() for s in species_blacklist]

    # Initial quantities
    jump_distance2 = jump_distance**2
    selection = Ions([poscar.ions[start_index]], [start_index])
    jumps = [0]

    # TODO: For some reason Pyright is being stupid and thinks
    # the Ions iterator is an iterator in Ion. Am  I accidentally tricking
    # it somehow?

    # From the selected ion, find neighbors in range
    first_hydrogen = True
    for (i, selected_ion), jump in zip(selection, jumps):  # type: ignore
        if jump >= extent:
            continue
        if (
            hydrogen_termination
            and not (first_hydrogen)
            and selected_ion.species == "H"
        ):
            continue
        poscar_cp = get_centered_around(poscar, selected_ion.position)
        poscar_cp._convert_to_cartesian()
        for j, ion in poscar_cp.ions:
            if j in selection.indices:
                continue
            if ion.species.lower() in species_blacklist:
                continue
            if j in index_blacklist:
                continue
            if (
                (poscar_cp.ions[i].position - poscar_cp.ions[j].position) ** 2
            ).sum() > jump_distance2:
                continue

            # Append a copy of the original ion
            selection.append(poscar.ions[j])
            selection.indices.append(j)
            # Record how many jumps it took to get here
            jumps.append(jump + 1)

        if first_hydrogen:
            first_hydrogen = False

    return selection
