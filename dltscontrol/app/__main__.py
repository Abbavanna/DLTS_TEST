""" 
Runs the DLTS Control application. This script has to be placed here, otherwise the pyinstaller package which builds the final program file doesn't work properly. 
"""

from pathlib import Path

from dltscontrol.app.icon import ICON_BASE64, ICON_STRING_ENCODING
from dltscontrol.app.manifest import manifest

import dltscontrol.apptk as apptk

# import application extensions
import dltscontrol.app.extensions

import os
import base64

DEFAULT_ICON_FILE_PATH = "icon_temp.ico"

def main(workingDirectory: Path = None, iconFilePath: Path = None):
    if workingDirectory is None:
        workingDirectory = Path(os.path.dirname(os.path.abspath(__file__)))
    if iconFilePath is None:
        iconFilePath = Path(DEFAULT_ICON_FILE_PATH)

    if not iconFilePath.exists():
        iconFilePath.write_bytes(base64.decodebytes(ICON_BASE64.encode(ICON_STRING_ENCODING)))

    try:
        apptk.Application(manifest, workingDirectory, iconFilePath).run()
    finally:
        if iconFilePath.exists():
            os.remove(iconFilePath)

if __name__ == "__main__":
    main()