import itertools as it
import re
from ast import literal_eval
from copy import deepcopy
from pathlib import Path
from typing import SupportsIndex

import numpy as np
from numpy.typing import NDArray


# Storage of position mode (direct or cartesian) is _only_ done in the POSCAR.
# The units on position of an ion makes no sense unless taken into context with
# a POSCAR.
class Ion(object):
    """
    An atom or ion contained within a POSCAR.
    Only has information that is immediately relevant to
    the ion itself. It has limited context of its container.
    """

    # Note: Index is not included here since it strictly applies
    # to the relative placement of the entry in the POSCAR file.
    # Indices are maintained where ion lists are relevant.
    def __init__(
        self,
        position: NDArray = np.zeros(3),
        species: str = "H",
        selective_dynamics: NDArray | tuple[bool, bool, bool] = np.ones(3, dtype=bool),
        velocity: NDArray = np.zeros(3),
    ):
        """
        Initialize an oject to contain ion information.
        """
        self.position = position
        self.species = species
        self.selective_dynamics = selective_dynamics
        self.velocity = velocity
        self._reinforce_types()

    def _reinforce_types(self):
        """
        Check the types and ensure they are consistent with expectations.
        """
        self.position = np.array(self.position, dtype=float)
        self.species = str(self.species)
        self.selective_dynamics = np.array(self.selective_dynamics, dtype=bool)
        self.velocity = np.array(self.velocity, dtype=float)

    def _apply_transformation(self, transform: NDArray, tol: float = 1e-8) -> None:
        """
        Given transformation matrix (3x3), transform the coordinates of the ion.
        """
        A = transform.reshape(3, 3)
        r = A @ self.position
        r = r * np.array(np.abs(r) > tol, dtype=int)
        self.position = r

    @staticmethod
    def list_to_bools(sd_tags:tuple[str,str,str]):
        """
        Method to convert selective dynamics flags from strings to bools.
        Enforces expected characters and length.
        """
        if len(sd_tags) != 3:
            raise RuntimeError("Bad selective dynamics length on ion!")
        converted_list = []
        for i in sd_tags:
            match i:
                case "T":
                    converted_list.append(True)
                case "F":
                    converted_list.append(False)
                case _:
                    RuntimeError("Bad selective dynamics character on ion!")
        return np.array(converted_list, dtype=bool)


# For use in POSCAR type hinting and ion portability
class Ions(list[Ion]):
    """
    __iter__() returns index first, adhering to enum style.
    Stores a list of Ion objects and allows easy iteration.
    Also stores a companion list of indices according to the POSCAR
    it was derived from; allowing for edits to POSCAR contents later.
    """

    def __init__(self, ions: list[Ion] = [], indices: list = []):
        self.indices: list[int] = indices
        return super().__init__(ions)

    # TODO: Fix this so Pyright stops complaining later?
    def __iter__(self):  # type: ignore
        for i, ion in zip(self.indices, super().__iter__()):
            yield i, ion

    # TODO: Revisit this deepcopy implementation. It relies on using the append
    # member function which can allow for breaking of index list.
    def __deepcopy__(self, memo: dict):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for _, ion in self:
            result.append(deepcopy(ion, memo))
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    # TODO: Revamp this to enforce a well kept index list by always having an index
    # associated with its corresponding ion
    def append(self, ion: Ion, index: int | None = None):
        if index is not None:
            self.indices.append(index)
        return super().append(ion)

    def pop(self, index: SupportsIndex = -1):
        self.indices.pop(index)
        return super().pop(index)


# Class for an INCAR since it's basically just a dictionary
class Incar(dict):
    # Use the normal dictionary constructor
    # Add a comments list on the side
    def __init__(
        self,
        tags: dict = {},
        sections: dict = {},
        inline_comments: dict = {},
        solo_comments=[],
    ):
        self.key_length = 8
        self.value_length = 8
        # Dictionary of sections with lists of tags within
        self.sections = sections
        # Dictionary of inline comments and their respective tags
        self.inline_comments = inline_comments
        # List of solitary comments and their sections
        self.solo_comments = solo_comments
        # A dictionary of all the VASP tags
        return super().__init__(tags)

    # Overwrite normal bitwise Or behavior
    def __or__(self, b):
        # TODO: Handle case where key is placed in different sections
        tags = dict(self) | dict(b)
        sections = self.sections | b.sections
        for k in sections.keys():
            try:
                sections[k] = list(set(self.sections[k] + b.sections[k]))
            except KeyError:
                pass
        inline_comments = self.inline_comments | b.inline_comments
        solo_comments = self.solo_comments + b.solo_comments
        return Incar(tags, sections, inline_comments, solo_comments)

    # In-place bitwise Or
    def __ior__(self, b):
        sections = self.sections | b.sections
        for k in sections.keys():
            try:
                sections[k] = list(set(self.sections[k] + b.sections[k]))
            except KeyError:
                pass
        self.sections = sections
        self.inline_comments |= b.inline_comments
        self.solo_comments += b.solo_comments
        return super().__ior__(b)

    # TODO: Pyright complains about this but I don't know what it means'
    def update(self, b):  # type: ignore
        self.__ior__(b)

    def __delitem__(self, key: str) -> None:
        # Delete an inline comment if it exists
        try:
            self.inline_comments.__delitem__(key)
        except KeyError:
            pass
        # Delete the entry from any sections
        for k, v in self.sections.items():
            if key in v:
                self.sections[k].remove(key)
        # Delete the entry in the dictionary
        return super().__delitem__(key)

    def remove(self, key: str) -> None:
        return self.__delitem__(key)

    def __section_str__(self, section: str) -> str:
        # Get the title first
        formatted_string = f"\n# {section}\n\n"
        # Then the solitary comments in one block
        local_solo_comments = [s[0] for s in self.solo_comments if s[1] == section]
        for comment in local_solo_comments:
            formatted_string += f"! {comment}\n"
        formatted_string += "\n" if len(local_solo_comments) > 0 else ""
        # Then the keys, values, and inline comments
        for key in self.sections[section]:
            formatted_string += self.__tag_str__(key)
        return formatted_string

    def __tag_str__(self, key: str) -> str:
        formatted_string = f"{key:<{self.key_length}} = "
        value = self[key]
        if type(value) is list:
            value = " ".join((str(i) for i in value))
        formatted_string += f"{str(value):<{self.value_length}}"
        try:
            formatted_string += f" ! {self.inline_comments[key]}"
        except KeyError:
            pass
        return formatted_string + "\n"

    def __str__(self) -> str:
        return self.to_rich_string()

    def to_simple_string(self) -> str:
        formatted_string = ""
        for key, value in self.items():
            if type(value) is list:
                value = " ".join((str(i) for i in value))
            formatted_string += f"{key} = {value}\n"
        return formatted_string.strip()

    def to_rich_string(self) -> str:
        formatted_string = ""
        # Get any tags that aren't in a section first
        sectioned_tag_set = set(
            it.chain.from_iterable((s for s in self.sections.values()))
        )
        orphaned_tags = list(set(self.keys()) - sectioned_tag_set)
        for key in orphaned_tags:
            formatted_string += self.__tag_str__(key)
        # Format for each section
        for section in self.sections:
            formatted_string += self.__section_str__(section)

        return formatted_string.strip()

    def to_file(self, file: str | Path, parents=True, simple=False) -> None:
        """
        Write the INCAR to the given file.
        """
        file = Path(file)
        parent = file.parent
        Path.mkdir(parent, parents=parents, exist_ok=True)
        with file.open("w") as f:
            if simple:
                f.write(self.to_simple_string())
            else:
                f.write(self.to_rich_string())

    @classmethod
    def from_file(cls, input: Path|str = "INCAR"):
        input_path = Path(input)
        tags = {}
        sections = {}
        inline_comments = {}
        solo_comments = []

        with input_path.open("r") as incar_file:
            incar_text = incar_file.readlines()
            current_section = None
            for line in incar_text:
                line = line.strip()
                # Skip empty lines
                if len(line) == 0:
                    continue
                # Error on malformed lines
                if line[0] not in ("#", "!") and "=" not in line:
                    raise RuntimeError(f"Malformed INCAR tag: {line}")

                # Determine if this is a section header, solitary comment,
                # or tag (optionally with inline comment).
                # Test the first character to determine the type of line
                match line[0]:
                    case "#":
                        # Format the section name to something consistent
                        current_section = line[1:].strip().capitalize()
                    case "!":
                        comment = line[1:].strip()
                        solo_comments.append((comment, current_section))
                    case _:
                        key, value = (s.strip() for s in line.split("=", maxsplit=1))
                        # Test if there is an inline comment and save it
                        if "!" in value or "#" in value:
                            comment_start = np.array([value.find("!"), value.find("#")])
                            comment_start *= -1 if -1 in comment_start else 1
                            comment_start = np.abs(comment_start.min())
                            comment = value[comment_start + 1 :].strip()
                            value = value[:comment_start].strip()
                            inline_comments[key] = comment
                        try:
                            # If there are spaces, parse it out as a list
                            if " " in value:
                                value = [literal_eval(v) for v in value.split(" ")]
                            # Otherwise, parse it as a single value
                            else:
                                value = literal_eval(value)
                        # If literal evaluation fails, leave it as a string
                        except ValueError:
                            pass
                        except SyntaxError:
                            pass
                        # Add the tag to the dictionary
                        if key in tags.keys():
                            print(f'Warning: Key "{key}" appears more than once!')
                            for k, v in sections.items():
                                if key in v:
                                    sections[k].remove(key)
                        tags[key] = value
                        # Skip the sectioning if this is an orphaned tag
                        if current_section is None:
                            continue
                        # If the section hasn't been created, do so
                        if current_section not in sections.keys():
                            sections[current_section] = []
                        # Add the tag to the section
                        sections[current_section].append(key)

        return cls(tags, sections, inline_comments, solo_comments)


# Class for containing POTCAR info
# Does not store POTCAR string, but can create it
class Potcar(object):
    """ """

    def __init__(self, potentials: list[str] = [], directory: Path|str = "."):
        self.potentials = potentials
        self.directory = Path(directory)
        if not (self.directory.exists()):
            raise RuntimeError("Provided potcar directory does not exist!")

    @classmethod
    def from_poscar(cls, input: str = "POSCAR", directory: str = "."):
        poscar = Poscar.from_file(input)
        return cls(list(poscar.species.keys()), directory)

    def generate_string(self) -> str:
        # Choose the LDA or PBE automatically if it isn't specified
        directory = Path(self.directory)
        if directory.name.lower() not in ["gga", "lda"]:
            if len(self.potentials) > 1:
                directory = Path(directory, "GGA")
            else:
                directory = Path(directory, "LDA")
        if not (directory.exists()):
            raise RuntimeError(
                f"Expected potcar directory `{directory}` does not exist"
            )

        # Create a list of paths for the species' POTCARs
        potential_paths = [Path(directory, sp, "POTCAR") for sp in self.potentials]

        # Return the POTCARs as one concatenated string
        contents = ""
        for sp in potential_paths:
            contents += sp.read_text()

        return contents

    def generate_file(self, output: Path|str = "POTCAR", parents: bool = True) -> None:
        # Choose the LDA or PBE automatically if it isn't specified
        output_path = Path(output)
        parent = output_path.parent
        Path.mkdir(parent, parents=parents, exist_ok=True)
        with output_path.open("w") as f:
            f.write(self.generate_string())


# Class to parse and store POSCAR data in a rich, type hinted, format
class Poscar(object):
    """ """

    def __init__(
        self,
        comment: str = "",
        scale: NDArray = np.ones(3, dtype=float),
        lattice: NDArray = np.identity(3, dtype=float),
        species: dict = {},
        selective_dynamics: bool = False,
        mode: str = "Direct",
        ions: Ions = Ions(),
        lattice_velocity: NDArray = np.zeros((3, 3)),
        mdextra: str = "",
    ):
        """
        Initialize a POSCAR from argument data only
        """
        self.comment = comment
        self.scale = scale
        self.lattice = lattice
        self.species = species
        self.selective_dynamics = selective_dynamics
        self.mode = mode
        self.ions = ions
        self.lattice_velocity = lattice_velocity
        self.mdextra = mdextra

    def __str__(self):
        """
        Automatic string conversion
        """
        return self.to_string()

    def _reconcile_ions(self):
        """
        Count the population of each species of ions and update
        the self contained species list.
        This is useful for ensuring agreement between ion counts
        and species populations since it's more intuitive to edit
        ions directly.
        """
        # Make sure the species list is in order
        species = {}
        for _, ion in self.ions:
            isp = ion.species.lower().capitalize()
            if species.__contains__(isp):
                species[isp] += 1
            else:
                species[isp] = 1
        self.species = species
        # Make sure the ions are sorted properly
        ions = []
        for sp in self.species.keys():
            mask = [i.species == sp for _, i in self.ions]
            ions += list(it.compress(self.ions, mask))
        self.ions = ions

    def _toggle_mode(self) -> None:
        """
        Change the position mode from direct to cartesian or vice-versa.
        """
        if self.is_direct():
            self._convert_to_cartesian()
        elif self.is_cartesian():
            self._convert_to_direct()
        else:
            raise RuntimeError(
                "Unrecognized mode descriptor when attempting to toggle!"
            )

    def _convert_to_direct(self, error=False) -> None:
        """
        Convert the mode to direct.
        Optionally raise a RuntimeError if it is already direct.
        """
        # Check to make sure it's not already direct
        if self.is_direct():
            if error:
                raise RuntimeError("POSCAR is already in direct mode.")
            return

        # Create the transformation matrix
        A = self.lattice.transpose()
        Ainv = np.linalg.inv(A)
        # Convert all ion positions to fractions of the lattice vectors and round to zero

        for i, _ in self.ions:
            self.ions[i]._apply_transformation(Ainv)

        # Change the mode string
        self.mode = "Direct"

    def _convert_to_cartesian(self, error=False) -> None:
        """
        Convert the mode to cartesian.
        Optionally raise a runtimeError if it is already cartesian.
        """
        # Check to make sure it's not already cartesian
        if self.is_cartesian():
            if error:
                raise RuntimeError("POSCAR is already in cartesian mode.")
            return

        # Convert all ion positions to fractions of the lattice vectors and round to zero
        # Create the transformation matrix and tolerance
        A = self.lattice.transpose()
        for i, _ in self.ions:
            self.ions[i]._apply_transformation(A)

        # Change the mode string
        self.mode = "Cartesian"

    def _constrain(self) -> None:
        """
        Make sure all ions lie within boundary of cell.
        """
        # Convert to direct
        converted = False
        if self.is_cartesian():
            self._convert_to_direct()
            converted = True

        # If any direct mode coordinate exceeds +-1
        # subtract the floor from that coordinate, keeping the fraction
        for i, ion in self.ions:
            self.ions[i].position = ion.position - ion.position // 1

        # Reconvert if necessary
        if converted:
            self._convert_to_cartesian()

    def is_cartesian(self) -> bool:
        """
        Return true if position mode is cartesian.
        """
        return self.mode[0].lower() in ("c", "k")

    def is_direct(self) -> bool:
        """
        Return true if position mode is direct.
        """
        return self.mode[0].lower() == "d"

    @classmethod
    def from_file(cls, poscar_file: Path|str):
        """
        Return a POSCAR object with data matching the provided poscar_file.
        """
        file_path = Path(poscar_file)

        with file_path.open("r") as f:
            # Read comment line
            s_comment = f.readline().strip()

            # Read scaling factor(s)
            scale = f.readline().strip().split()
            if len(scale) == 1:
                scale = scale * 3
            elif len(scale) != 3:
                raise ValueError(
                    "Wrong number of scaling \
                                 factors supplied in POSCAR!"
                )
            s_scale = np.array(scale, dtype=float)

            # Read lattice vectors
            vec = np.array([], dtype=float)
            for _ in range(3):
                line = f.readline()
                v = np.array(line.strip().split(), dtype=float)
                vec = np.append(vec, v)
            s_lattice = vec.reshape((3, 3))

            # Mandatory check, species names
            # Enforce capitalization
            line = f.readline()
            species = []
            if line.replace(" ", "").strip().isalpha():
                species = [sp.lower().capitalize() for sp in line.split()]
                line = f.readline()

            # Read ions per species
            counts = line.strip().split()
            # Handle the optional case of no species specified
            if len(species) == 0:
                species = ["H" + str(i + 1) for i in range(len(counts))]
            elif len(species) != len(counts):
                raise RuntimeError("Mismatch between species and ion counts!")
            s_species = {
                str(sp.lower().capitalize()): int(ct) for sp, ct in zip(species, counts)
            }

            # Optional check, selective dynamics
            line = f.readline()
            s_selective_dynamics = False
            if line[0].lower() == "s":
                s_selective_dynamics = True
                line = f.readline()

            # Read ion position mode
            if line[0].lower() in ("c", "k"):
                s_mode = "Cartesian"
            elif line[0].lower() == "d":
                s_mode = "Direct"
            else:
                raise RuntimeError("Unknown position mode")

            # TODO: Strict type hinting HATES this section
            # Read in ion
            s_ions = Ions()
            ions = it.chain.from_iterable([[sp] * c for sp, c in s_species.items()])
            for i, sp in enumerate(ions):
                line = f.readline().split()
                r = np.array(line[0:3], dtype=float)
                sd = ("True",) * 3
                if s_selective_dynamics:
                    sd = np.array(
                        tuple([False if f == "F" else True for f in line[3:6]]),
                        dtype=bool,
                    )
                v = np.zeros(3)
                s_ions.append(Ion(r, sp, sd, v), i)  # type: ignore

            # Leave velocity as zero
            # Leave mdextra as empty

            return cls(
                s_comment,
                s_scale,
                s_lattice,
                s_species,
                s_selective_dynamics,
                s_mode,
                s_ions,
            )

    def to_string(self) -> str:
        """
        Return a formatted string of the POSCAR dictionary as would be found in a file.
        """
        # Write comment line
        poscar_string = ""
        poscar_string += self.comment + "\n"

        # Write scaling factor
        if np.allclose(self.scale, [self.scale[0]] * 3):
            poscar_string += "  {:>11.8f}\n".format(self.scale[0])
        else:
            poscar_string += "  {:>11.8f}  {:>11.8f}  {:>11.8f}\n".format(*self.scale)

        # Write lattice vectors
        for i in self.lattice:
            poscar_string += "    {:>11.8f}  {:>11.8f}  {:>11.8f}\n".format(*i)

        # Write the species names
        line = ""
        # If all the species are placeholder H0, H1, H2, ..., then skip writing this line
        if False in [bool(re.match(r"H[0-9]+", sp)) for sp in self.species.keys()]:
            line += " ".join([f"{sp:>6s}" for sp in self.species.keys()]) + "\n"
        else:
            line = ""
        poscar_string += line

        # Write species numbers
        line = ""
        line += " ".join([f"{c:>6d}" for c in self.species.values()]) + "\n"
        poscar_string += line

        # Write selective dynamics if enabled
        if self.selective_dynamics:
            poscar_string += "Selective dynamics\n"

        # Write position mode
        poscar_string += self.mode + "\n"

        # Write the ion positions with selective dynamics tags if needed
        for _, ion in self.ions:
            line = "{:>11.8f}  {:>11.8f}  {:>11.8f}".format(*ion.position)
            if self.selective_dynamics:
                line += " {:>1s} {:>1s} {:>1s}".format(
                    *["T" if t else "F" for t in ion.selective_dynamics]
                )
            poscar_string += line + "\n"

        # TODO: Write littec vector and ion velocities and MD extra

        return poscar_string

    def to_file(self, file: str | Path, parents=True) -> None:
        """
        Write the POSCAR to the given file.
        """
        file = Path(file)
        parent = file.parent
        Path.mkdir(parent, parents=parents, exist_ok=True)
        with file.open("w") as f:
            f.write(self.to_string())

    def generate_potcar_str(self, potcar_dir: str = ".") -> str:
        """
        Generate a POTCAR for the current POSCAR.
        """
        # Define pseudopotential path
        potcar = Potcar(list(self.species.keys()), potcar_dir)
        return potcar.generate_string()

    def generate_potcar_file(
        self, potcar_dir: str = ".", output: str = "POTCAR", parents=True
    ) -> None:
        """
        Generate and write a POTCAR for the current POSCAR.
        """
        potcar = Potcar(list(self.species.keys()), potcar_dir)
        potcar.generate_file(output)

    def edit_ions(self, ions: Ions):
        """
        Overwrite matching ions in the POSCAR by index.
        """
        for i, ion in ions:
            self.ions[i] = ion
        self._reconcile_ions()

    def remove_ions(self, ions: Ions):
        """
        Remove the ions provided in the list according to index.
        """
        for i, _ in ions:
            self.ions.pop(i)
        self._reconcile_ions()
