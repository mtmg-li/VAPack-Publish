# VAPack

A collection of utilities for generation and manipulation of input files for the Vienna Ab-initio Simulation Package (VASP).

_More to come!_

## Installation

There is currently no automated or standardized way to "install" VAPack.
To conveniently call the vapack scripts from anywhere on your system, you should create an alias in your shell environment.
Keep in mind that this alias will call the version of the script in the most recent branch you switched to.
If you're frequently switching, such as for development, consider making a separate directory that remains on the master branch for your alias.

### Bash

Edit your `.bashrc` file, likely located in your home directory.
Add the line
```bash
alias vapack="<vapack directory>/vapack.py"
```
where `<vapack directory>` is the location of your copy of the vapack repository.

### Zsh

Edit your `.zshrc` file, likely located in your home directory.
Add the line
```bash
alias vapack="<vapack directory>/vapack.py"
```
where `<vapack directory>` is the location of your copy of the vapack repository.

### Fish

Enter the command
```bash
alias --save vapack="<vapack directory>/vapack.py"
```
where `<vapack directory>` is the location of your copy of the vapack repository.
