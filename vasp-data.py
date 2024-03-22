import numpy as np
from pathlib import Path

class SlurmScript:
    """
    Store, manipulate, and write information to submit a job to the slurm queuing system
    """

    # Create blank variables
    def __init__(self):
        self.job = ''
        self.output = ''
        self.time_limit = ''
        self.N = 0
        self.n = 0
        self.queue = ''

    # Read and populate the information from a file
    def from_file(self, file:Path):
        with file.open() as f:
            for line in f.readlines():
                args = line.split()
                
                if not(args[0] == '#!SBATCH'):
                    continue

                match args[1]:
                    case '-J':
                        self.job = str(args[2])
                    case '-o':
                        self.output = str(args[3])
                    case '-t':
                        self.time_limit = str(args[3])
                    case '-N':
                        self.N = int(args[3])
                    case '-n':
                        self.n = int(args[3])
                    case '-p':
                        self.queue = str(args[3])
    
