#!/usr/bin/env python3

"""
Command line program that provides easy access to tools in Vasp Tool Kit
"""

from copy import deepcopy
from pathlib import Path

import click
import numpy as np
import numpy.typing as npt

import vapack.extensions as vext
from vapack.types import Incar, Ion, Ions, Poscar, Potcar

# Notes to whoever attempts to maintain this:
#
# 1. While default values for run function arguments exist
#    in the function definition, they are overridden by the
#    argument parser default values, which if not specified
#    is None.
#
# 2. This is now constructed using Click, which does what
#    I had previously implemented, but better. See:
#    https://palletsprojects.com/projects/click/


@click.group()
def cli():
    pass


@cli.command(help="Convert a POSCAR between direct and cartesian.")
@click.argument("input", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.option(
    "-m",
    "--mode",
    help="Convert to cartesian or direct, or toggle the mode",
    type=click.Choice(["cartesian", "c", "direct", "d"], case_sensitive=False),
)
@click.option("-o", "--output", help="Output file", type=click.Path())
@click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
@click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
def convert(
    input: Path | str,
    mode: str | None = None,
    output: Path | str | None = None,
    verbose: bool = False,
    write: bool = True,
) -> None:
    # Determine output location
    input_path = Path(input)
    output_path = (
        Path(f"{input_path.stem}_convert{input_path.suffix}")
        if output is None
        else Path(output)
    )

    # Verbose message
    if verbose:
        print(f"Converting ion position mode of {input_path}")

    # Read in file
    poscar = Poscar.from_file(input_path)

    # If toggle mode, choose the correct
    if mode is None:
        poscar._toggle_mode()
    elif mode.lower().startswith("c"):
        poscar._convert_to_cartesian()
    elif mode.lower().startswith("d"):
        poscar._convert_to_direct()
    else:
        raise RuntimeError("Unknown conversion")

    # Write the new POSCAR
    if write:
        poscar.to_file(output_path)

    if verbose:
        if not write:
            print("No changes written")
        else:
            print(f"Changes written to {output_path}")


@cli.command(help="Add vacuum layers to a given POSCAR")
@click.argument("input", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.argument("depth", type=float, nargs=3)
@click.option(
    "-o",
    "--output",
    help="Output file",
    type=click.Path(readable=True, dir_okay=False, path_type=Path),
)
@click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
@click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
def vacuum(
    input: str,
    depth: npt.NDArray,
    output: str | None = None,
    verbose: bool = False,
    write: bool = False,
) -> None:
    # Determine output location
    input_path = Path(input)
    output_path = (
        Path(f"{input_path.stem}_vacuum{input_path.suffix}")
        if output is None
        else Path(output)
    )

    # Verbose message
    if verbose:
        click.echo(f"Adding vacuum depth {depth} Å to {input_path}")

    # Read in the file
    poscar = Poscar.from_file(input_path)

    # Convert the POSCAR to cartesian
    poscar._convert_to_cartesian()

    # TODO: Interpret the depth, which may be 3 independent values

    # TODO: Take into account non-unity scaling factors

    # Add the vacuum layer in only the c-direction (roughly)
    # Take the 3 valued depth, cast to 3x3 diagonal matrix, and add to lattice
    if type(depth) is not np.array:
        depth = np.array(depth)
    poscar.lattice += np.diag(depth)

    # Write the new POSCAR
    if write:
        poscar.to_file(output_path)

    # Verbosity messages
    if verbose:
        if not write:
            click.echo("No changes written")
        else:
            click.echo("Changes written to {}".format(output_path))


@cli.command(help="Create a POTCAR from a POSCAR or list of potentials")
@click.argument("input", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.option(
    "-p",
    "--potentials",
    type=str,
    multiple=True,
    help="Create the POTCAR according to a list of potentials instead",
)
@click.option("--recommended/--no-recommended", default=True, help="Use recommended pseudopotentials. Doesn't apply to manual selections.")
@click.option("--lda/--no-lda", default=None, help="Use the LDA pseudopotentials instead of PBE")
@click.option("--gw/--no-gw", default=False, help="Use GW pseudopotentials instead of standard")
@click.option(
    "-d",
    "--directory",
    type=click.Path(readable=True, file_okay=False, path_type=Path),
    default="./potcar",
    help="Directory of POTCAR folders",
)
@click.option(
    "-o", "--output", help="Output file", type=click.Path(), default=Path("./POTCAR")
)
@click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
@click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
def potcar(
    input: str,
    output: Path | str = Path("./POTCAR"),
    potentials: list = [],
    directory: str = ".",
    recommended: bool = False,
    lda: bool | None = None,
    gw: bool = False,
    verbose: bool = False,
    write: bool = False,
):
    # Cast input, output, and directory to paths
    input_path = Path(input)
    output_path = Path(output)
    directory_path = Path(directory)

    # Initialize the species list
    species = []

    # If the POSCAR is 'none', then use the provided list
    if input_path.stem.lower() == "none":
        if len(potentials) < 1:
            raise RuntimeError(
                'Since POSCAR is "none", a potentials list must be provided!'
            )
        species = potentials

    # If the POSCAR is a file (not 'none')
    else:
        poscar = Poscar.from_file(input_path)
        species = list(poscar.species.keys())

    # Create the potcar object
    potcar = Potcar(species, directory_path)

    # Verbose species message
    if verbose:
        if lda is not None:
            ps_type = "LDA" if lda else "GGA"
            ps_type = ps_type
        elif len(species) > 1:
            ps_type = "(auto) GGA"
        else:
            ps_type = "(auto) LDA"
        print(f"Using {ps_type} potentials")
    
        if recommended:
            print("Substituting for recommended pseudopotentials")
        
        if gw:
            print("Using GW pseudopotentials")
        else:
            print("Using standard pseudopotentials")

    # Generate and write the potcar
    if not write:
        if verbose:
            print("No changes written")
        return

    potcar.generate_file(
        output_path, use_recommended=recommended, use_lda=lda, use_gw=gw
    )

    if verbose:
        print("Changes written to {}".format(output_path))


@cli.command(
    help="Change the selective dynamics flags for all ions inside the defined box"
)
@click.argument("input", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.option(
    "-x",
    "--x-range",
    nargs=2,
    type=float,
    help="Range in x to select. If unspecified, all x coords are viable.",
)
@click.option(
    "-y",
    "--y-range",
    nargs=2,
    type=float,
    help="Range in y to select. If unspecified, all y coords are viable.",
)
@click.option(
    "-z",
    "--z-range",
    nargs=2,
    type=float,
    help="Range in z to select. If unspecified, all z coords are viable.",
)
@click.option(
    "-d",
    "--dynamics",
    nargs=3,
    type=str,
    default=["T", "T", "T"],
    help="Selective dynamics flags to apply",
)
@click.option(
    "-m",
    "--mode",
    help="Treat ranges in cartesian or direct mode.",
    type=click.Choice(["cartesian", "c", "direct", "d"], case_sensitive=False),
)
@click.option(
    "-o",
    "--output",
    help="Output file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
)
@click.option(
    "--preserve/--no-preserve",
    default=False,
    help="Preserve the flags of ions that aren't modified",
)
@click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
@click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
def slabfreeze(
    input: Path | str,
    x_range: list[float] | None = None,
    y_range: list[float] | None = None,
    z_range: list[float] | None = None,
    dynamics: tuple[str, str, str] | npt.NDArray = ("T", "T", "T"),
    mode: str | None = None,
    output: Path | str | None = None,
    preserve: bool = False,
    verbose: bool = False,
    write: bool = True,
):
    # Read the input file
    input_path = Path(input)
    poscar = Poscar.from_file(input)

    # Initialize the output path
    output_path = (
        Path(f"{input_path.stem}_frozen{input_path.suffix}")
        if output is None
        else Path(output)
    )

    # Verbose message
    if verbose:
        print(f"Creating POSCAR from {input_path}")
        print("Using {} mode".format("auto" if mode is None else mode))
        range_str = []
        if x_range is not None:
            range_str.append(f"{x_range[0]} <= x <= {x_range[1]}")
        if y_range is not None:
            range_str.append(f"{y_range[0]} <= y <= {y_range[1]}")
        if z_range is not None:
            range_str.append(f"{z_range[0]} <= z <= {z_range[1]}")
        range_str = ", ".join(range_str)
        print(f"Applying selective dynamics {dynamics} to ions inside {range_str}")

    # TODO: Fix the type hinting here
    # Convert the dimensions to bool
    dynamics = Ion.list_to_bools(dynamics)  # type: ignore

    # Get box selection of ions
    selection = vext.get_select_box(poscar, x_range, y_range, z_range, mode)

    # Change the selective dynamics of selection
    for i, _ in enumerate(poscar.ions):
        d = dynamics
        if i not in selection.indices:
            if preserve:
                continue
            # poscar.ions[i].selective_dynamics = np.array([True]*3, dtype=bool)
            d = Ion.list_to_bools(("T", "T", "T"))
        poscar.ions[i].selective_dynamics = d
    poscar.selective_dynamics = True

    # Final verbose message
    if verbose:
        print(f"Switched {len(selection)}/{len(poscar.ions)} ions")

    # Write the modified poscar
    poscar.to_file(output_path)


@cli.command(
    help="Linearly interpolate images for a NEB calculation from two POSCAR files"
)
@click.argument("file1", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.argument("file2", type=click.Path(readable=True, dir_okay=False, path_type=Path))
@click.option(
    "-i",
    "--images",
    help="Number of interpolated images to create",
    type=int,
    default=1,
)
@click.option("--selective-dynamics", is_flag=True, default=True, help="Enable reading of selective dynamics tags")
# @click.option(
#     "--center/--no-center",
#     default=False,
#     help="Center the POSCARS about center of mass",
# )
@click.option(
    "--boundary-resolver",
    help="How to resolve boundary cross cases",
    type=click.Choice(["first", "last"], case_sensitive=False),
)
@click.option(
    "--dynamics-resolver",
    help="How to resolve disagreements between selective dynamics",
    type=click.Choice(["first", "last", "free", "fixed"]),
)
@click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
@click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
def interpolate(
    file1: str,
    file2: str,
    images: int = 1,
    # center: bool = False,
    selective_dynamics: bool = False,
    boundary_resolver: str | None = None,
    dynamics_resolver: str | None = None,
    verbose: bool = False,
    write: bool = False,
):
    # Load the anchors
    poscar1 = Poscar.from_file(file1)
    poscar2 = Poscar.from_file(file2)

    # TODO: Check if the headers match
    # Make sure the files are in the same coordinate space
    if poscar2.mode != poscar1.mode:
        poscar2._toggle_mode()

    # Ensure that there are the same number of ions in each
    if len(poscar1.ions) != len(poscar2.ions):
        raise RuntimeError("Number of ions do not match!")

    # Ensure no ions cross the unit cell boundaries
    boundary_resolution_indices = []
    # TODO: Pyright is being tricked into thinking this is an iterator for an Ion,
    # not an iterator for an Ions. Figure out why.
    for (i, ion1), (_, ion2) in zip(poscar1.ions, poscar2.ions):  # type: ignore
        if (np.sign(ion1.position) * np.sign(ion2.position)).sum() != 3:
            print(f"Warning: Ion {i} crossed boundary between anchors!")
            boundary_resolution_indices += [i]

    # Template the output poscar image
    image_template = deepcopy(poscar1)

    # Disable selective dynamics unless told not to change it
    if not (selective_dynamics):
        image_template.selective_dynamics = False

    # Interpolate between ion positions and save to template
    boundary_resolver_message_printed = False
    dynamics_resolver_message_printed = False
    for i in range(images + 2):
        # Erase the existing ion data in the template
        image_template.ions = Ions([], [])
        # Get interpolated ion positions
        for (j, ion1), (_, ion2) in zip(poscar1.ions, poscar2.ions):  # type: ignore
            new_ion = Ion()
            new_ion.species = ion1.species
            # Handle edge cases where there'll be bad interpolation
            if j in boundary_resolution_indices:
                if not (boundary_resolver_message_printed):
                    boundary_resolver_message_printed = True
                    print(f'Resolving case on ion {j} with "{boundary_resolver}"')
                if boundary_resolver == "first":
                    if i < images + 1:
                        new_ion.position = ion1.position
                    else:
                        new_ion.position = ion2.position
                elif boundary_resolver == "last":
                    if i == 0:
                        new_ion.position = ion1.position
                    else:
                        new_ion.position = ion2.position
            # For normal cases, go by normal linear interpolation
            else:
                new_ion.position = (
                    ion1.position + (ion2.position - ion1.position) / (images + 1) * i
                )
            # Add selective dynamics tags if appropriate
            if selective_dynamics:
                if not (
                    np.array_equal(ion1.selective_dynamics, ion2.selective_dynamics)
                ):
                    dynamics_resolver = (
                        "free" if dynamics_resolver is None else dynamics_resolver
                    )
                    if not (dynamics_resolver_message_printed):
                        dynamics_resolver_message_printed = True
                        print(
                            f"Ion {j} selective dynamics disagreed. Resolving with {dynamics_resolver}."
                        )
                    if dynamics_resolver == "first":
                        new_ion.selective_dynamics = ion1.selective_dynamics
                    elif dynamics_resolver == "last":
                        new_ion.selective_dynamics = ion2.selective_dynamics
                    elif dynamics_resolver == "free":
                        new_ion.selective_dynamics = np.array([True] * 3)
                    elif dynamics_resolver == "fixed":
                        new_ion.selective_dynamics = np.array([False] * 3)
                    else:
                        # New ion object default (currently all true)
                        pass
                else:
                    new_ion.selective_dynamics = ion1.selective_dynamics
            image_template.ions.append(new_ion, j)
        # Create output path
        output_path = Path(".", str(i).zfill(2), "POSCAR")
        # Write the file
        image_template.to_file(output_path)


# @cli.command(help="Generate an INCAR file from the provided templates")
# @click.option(
#     "-s", "--source", multiple=True, type=str, help="Names of source templates"
# )
# @click.option("-n", "--name", type=str, help="System name")
# @click.option(
#     "-d",
#     "--template-dir",
#     type=click.Path(readable=True, file_okay=False, exists=True, path_type=Path),
#     default=Path("./templates"),
#     help="Template directory",
# )
# @click.option(
#     "-o",
#     "--output",
#     help="Output file",
#     type=click.Path(readable=True, dir_okay=False, path_type=Path),
#     default=Path("./INCAR"),
# )
# @click.option("--verbose/--no-verbose", help="Print operation messages to stdout")
# @click.option("--write/--no-write", default=True, help="Enable/disable writing changes to disk.")
# def genincar(
#     sources: list[str],
#     output: Path | str = Path("./INCAR"),
#     template_dir: Path | str = "templates/incar/",
#     name: str | None = None,
#     verbose: bool = False,
#     write: bool = False,
# ):
#     # Set the template containing directory
#     template_dir = Path(template_dir)
#     # Get paths to the templates and ensure they exist
#     template_files = [Path(template_dir, s) for s in sources]
#     for f in template_files:
#         if not (f.exists()):
#             raise RuntimeError("Could not find template")
#     # Iterate through the templates and construct the incar
#     incar = Incar()
#     for f in template_files:
#         incar |= Incar.from_file(f)

#     # Set the system name
#     incar["System"] = str(name)

#     # Write the file
#     incar.to_file(output)


if __name__ == "__main__":
    cli()
