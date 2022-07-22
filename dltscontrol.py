""" 
Starts the DLTS Control Application. 
"""

from pathlib import Path

from dltscontrol.app.__main__ import main

import os

if __name__ == "__main__":
    main(Path(os.path.dirname(os.path.abspath(__file__))))

# ^^,