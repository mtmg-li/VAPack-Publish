# VAPack

A collection of utilities for generation and manipulation of input files for the Vienna Ab-initio Simulation Package (VASP).

There is a command line interface for making common adjustments to simulation files and an importable library that will allow you to use the features in any script or interactive interpreter you wish.

## Installation

VAPack now follows a source-tree layout and includes build instructions.
Before building VAPack, it's recommended to have a virtual environment to install to.
Your Python environment must have `build` installed, which you can get with `pip install --upgrade build`.
From there, simple run build with `python -m build` while in the top level of VAPack.
Build should automatically find and package all the project files into an archive that gets placed into a `./dist` directory.
Install this archive using pip with the command `pip install ./dist/vapack-{ver}.tar.gz`, where `ver` is the package version.

## Usage

VAPack is now available in your virtual environment, anywhere in your system.
You can call the command line tool by simply typing `vapack`.
You can also import the various modules in the package by adding `import vapack.{module}` into your scripts.
