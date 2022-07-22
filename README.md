# DLTS Control G2

This project contains the second generation DLTS (DVD Laser Tag System) Control application. A software tool completely written in python 3 to control, acquire data from and communicate in general with a DLTS.

## Getting Started

To run or contribute to the software you have to make sure that your python environment meets all requirements listed in the [requirements file](requirements.txt) and [windows-only requirements file](requirements_windows.txt). In order to install all requirements into your current python environment you can use the package installer `pip`:

`pip3 install -r requirements.txt`

Additionally on Windows:

`pip3 install -r requirements_windows.txt`

## How To Run

After all requirements have been installed you can start the application by executing the [application start script](dltscontrol.py):

`python3 dltscontrol.py`

On Windows:

`py dltscontrol.py`

## How To Contribute

The application code is located in the package [dltscontrol.app](dltscontrol/app). It is based on the tk/tcl gui framework based [apptk application model](dltscontrol/apptk.py) and uses the [dlts communication API](dltscontrol/dlts.py) for DLTS communication. To extend the existing application, like adding new scans or gui-elements, take a look at the [examples module](dltscontrol/app/examples.py) which covers and explains a few rudimentary extensions. Please be aware that these examples don't cover the whole extension potential. Therefore you should also rummage in some of the existing extensions which are all listed in the [extenions file](dltscontrol/app/extensions.py) to get even more knowledge on how to extend the application. To understand how the apptk and dlts module work is mostly essential for creating any new extension.

Don't forget to add any new package requirements of your extensions to the requirements file(s) mentioned above.
