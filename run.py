#!/usr/bin/env python3
import sys
import os

# Ensure the current directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from SPARC.main import main

if __name__ == "__main__":
    main()
