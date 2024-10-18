# VAPack

A collection of utilities for generation and manipulation of input files for the Vienna Ab-initio Simulation Package (VASP).

There is a command line interface for making common adjustments to simulation files and an importable library that will allow you to use the features in any script or interactive interpreter you wish.

## Build

VAPack now follows a source-tree layout and includes build instructions.
Before building VAPack, it's recommended to have a virtual environment to install to.
Your Python environment must have `build` installed, which you can get with `pip install --upgrade build`.
From there, simple run build with `python -m build --wheel` while in the top level of VAPack.
Build should automatically find and package all the project files into a wheel file (`.whl`) that gets placed into a new `./dist` directory.

## Install

After downloading or building the package, install it into your virtual environment using pip with `pip install vapack-{ver}-py3-none-any.whl` where `ver` is the package version.

## Usage

VAPack is now available in your virtual environment, anywhere in your system.
You can call the command line tool by simply typing `vapack`.
You can also import the various modules in the package by adding `import vapack.{module}` into your scripts.
