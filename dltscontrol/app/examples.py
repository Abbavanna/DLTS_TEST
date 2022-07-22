"""
Extension examples.

Uncomment the import of this example in the extenions.py file to see how the following examples work in the actual application.
"""

""" Extension: Adding a new main window and a new dialog. 

This example demonstrates how to add a new main window and a new dialog to the application. Additionally it shows a few basic dlts 
communication tasks.
"""

from dltscontrol.apptk import Applet

from dltscontrol.app.core import OkAbortDialog, IDltsComponent

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

class DltsSetter(Applet, IDltsComponent):
    """ The new main window of the application.
    
    Since the whole application is based on the `dltscontrol.apptk` module you have to inherit from `dltscontrol.apptk.Applet` in order 
    to add a new main window to the application. The derived class `DltsSetter` then represents the main window of the application.

    DLTS communication is accomplished with the `dltscontrol.dlts` module and has been integrated into the application through `dltscontrol.apptk.Service`s.
    To get access to the DLTS you have to request a `dltscontrol.app.core.DltsService`. The `dltscontrol.app.core.IDltsComponent` interface provides some
    convenient methods to get access to a DLTS much easier. Once you derive from that interface you can simply call `self.getDlts` which returns either a
    connected `dltscontrol.dlts.Dlts` instance, `None` or raises an exception if something goes wrong. There is also a similar interface to get easy access
    to an `dltscontrol.app.core.IUserConfig` called `dltscontrol.app.core.IUserConfigComponent`.   
    
    This new window shows four buttons which allow the user to send and set some dlts values.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)
        # the constructors arguments should never be used

        # GUI creation and configuration is usually done in the constructor using tkinter of course

        # set the title of the actual window on screen
        self.Window.title("DLTS Setter")

        # create four button
        buttonX = ttk.Button(self.Window, text = "Set X", command = self.onSetXClick)
        buttonY = ttk.Button(self.Window, text = "Set Y", command = self.onSetYClick)
        buttonZ = ttk.Button(self.Window, text = "Set Z", command = self.onSetZClick)
        buttonLaser = ttk.Button(self.Window, text = "Set Laser Intensity", command = self.onSetLaserIntensityClick)

        # place the buttons
        buttonX.pack(side = tk.LEFT)
        buttonY.pack(side = tk.LEFT)
        buttonZ.pack(side = tk.LEFT)
        buttonLaser.pack(side = tk.LEFT)
    
    def askIntegerValue(self) -> int:
        """ Opens a dialog and waits for it to get finished. Returns the dialog's result afterwards. """

        # open a integer dialog to ask the suer for an integer
        dialog = self.getContext().openDialog(IntegerDialog)

        # wait for result/dialogs gets closed and return it
        return dialog.waitForResult()

    def onSetXClick(self):
        """ Called when the user clicks on the 'Set X' button. """
        
        # ask the user for an integer
        value = self.askIntegerValue()

        # if the dialog hasn't been aborted
        if value is not None:

            # get the dlts
            dlts = self.getDlts()

            # set the value if the dlts is available
            if dlts is not None:
                dlts.setX(value)

    def onSetYClick(self):
        """ Called when the user clicks on the 'Set Y' button. """
        value = self.askIntegerValue()

        if value is not None:
            dlts = self.getDlts()

            if dlts is not None:
                dlts.setY(value)

    def onSetZClick(self):
        """ Called when the user clicks on the 'Set Z' button. """
        value = self.askIntegerValue()

        if value is not None:
            dlts = self.getDlts()

            if dlts is not None:
                dlts.setZ(value)
    
    def onSetLaserIntensityClick(self):
        """ Called when the user clicks on the 'Set Laser Intensity' button. """
        value = self.askIntegerValue()

        if value is not None:
            dlts = self.getDlts()

            if dlts is not None:
                dlts.setLaserIntensity(value)

class IntegerDialog(OkAbortDialog):
    """ Dialog to ask for an integer. 
    
    If you want to create a new dialog for the application you usually create a dialog interface first. It defines the general behavior 
    of the dialog without creating any graphical components. To create a new dialog you have to derive from `dltscontrol.apptk.Dialog`. 
    
    In this example the dialog dervies from `dltscontrol.app.core.OkAbortDialog` which already implements an 'ok abort behavior' meaning 
    that if the user hits the return/enter key the method `self._onOk` is called and if the user hits the escape or the window close button 
    the method `self._onAbort` is called. The dialog assigns `None` to `self.Result` automatically if it has been closed without providing 
    a result before.

    Dialog interface are used to open dialogs by calling `self.getContext().openDialog(DialogInterface)` in any application component. The 
    actual dialog interface implementation is then searched in the application's manifest and instantiated if found. That makes it possible
    to have and replace any implementation without changing the components which depend on the dialog interface since the dialog interface
    always stays the same no matter how the dialog is going to look like on screen.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        # a dialog interface doesn't have any gui

    def _onOk(self):
        """ Called when the user wants to submit his enetered value. """
        self.Result = self.getIntegerValue()
        self.close()

    def _onAbort(self):
        """ Called when the user wants to abort. """
        self.close()

    def setIntegerValue(self, value: int):
        """ Sets the integer value of the dialog also in the gui. """
        raise NotImplementedError

    def getIntegerValue(self) -> int:
        """ Returns the integer value of the dialog stated in the gui. """
        raise NotImplementedError

class StandardIntegerDialog(IntegerDialog):
    """ Standard implementation of an `IntegerDialog`.
    
    The actual implementation of a dialog needs to provide an actual gui. This implementation creates a simple label and entry to provide an integer value.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Give me an integer!")

        # variable to easily connect to the entry value
        self._variable = tkext.IntNoneVar(self.Window)
        
        label = ttk.Label(self.Window, text = "Enter your integer value:")
        entry = tkext.IntEntry(self.Window, textvariable = self._variable)

        label.pack(side = tk.LEFT)
        entry.pack(side = tk.LEFT)

    def setIntegerValue(self, value):
        self._variable.set(value)

    def getIntegerValue(self):
        return self._variable.get()

""" 
After all components have been implemented they have to get inserted into the application's manifest. Only actual instantiatable implementations can
be inserted. This should be done always at the end of a module so that it can be seen and modified easily. The new extenion has to be imported in the 
extenions.py file in order get integrated.
"""

from dltscontrol.app.manifest import manifest

# register applet with a menu name and as root applet
manifest.insert(DltsSetter, entry = "Dlts Setter", root = True)

# register standard integer dialog implementation
manifest.insert(StandardIntegerDialog)

""" Extension: Adding a new dlts scan. 

This extension shows how to add and integrate a new scan to the application. This also includes all necessary GUI component to create and configure such
a scan.

In this example the new scan scans the DUT for bit-flips which of course doesn't actually work unless it has been implemented in the dlts protocol and firmware. 
Per scan position the dlts sends five bytes in which the first four contain the first register address at which a bit-flip happend and the last one contains 
the total number of registers in which a bit-flip happened.

A new scan has to be implemented using the `dltscontrol.dlts` module. Since most scan are "standard" scans they can leverage from the `dltscontrol.dlts.Scan`
class. It implements already the basic scan behavior and provides a few command hooks to communicate with the dlts. Scans provide data through a list of 
`dltscontrol.dlts.IScanDataPoint`s and another list of `dltscontrol.dlts.IScanImage`s. Those two interfaces have to be implemented first. A scan data point 
contains the raw data acquired at a single scan position and its interpretation. A scan image consists of processed scan data points whose interpreted raw
data has been ordered and written into a `numpy.ndarray`. Scan images are usually of the most interest since the are usually depictable.
"""

from dltscontrol.dlts import DltsConstants, DltsCommand, DltsConnection, Scan, IScanDataPoint, ScanDataPoint, ScanImage

from dltscontrol.app.core import OkAbortDialog
from dltscontrol.app.scanning import ScanCreationService, StandardScanCreationPanel, StandardStandardScanCreationPanel, \
    ScanCreationDialog, StandardScanCreationDialog

class BitFlipScanConstants:

    DATA_POINT_BYTE_COUNT = 5 # register address size is 4 bytes

    SCAN_START_COMMAND = "asb" # action scan bit-flip

class IBitFlipScanDataPoint(IScanDataPoint):
    """ A scan data point which provides an address of a register in which a bit-flip happened and total number of registers in which bit-flips happened. """

    def getFirstFlippedRegisterAddress(self) -> int:
        """ The first address of a register in which a bit-flip happended at this scan position. """
        raise NotImplementedError

    def getNumberOfFlippedRegisters(self) -> int:
        """ The total number of registers in which a bit-flip happened at this scan position. """
        raise NotImplementedError

class BitFlipScanDataPoint(ScanDataPoint, IBitFlipScanDataPoint):
    """ The scan data point of a `BitFlipScan`. Consists of five bytes. First four: Register address. Fifth: Number of registers. """

    def __init__(self, rawData):
        super().__init__(rawData)

    def getFirstFlippedRegisterAddress(self):
        return int.from_bytes(self.RawData[:-1], DltsConstants.DLTS_INT_BYTE_ORDER)

    def getNumberOfFlippedRegisters(self):
        return int.from_bytes(self.RawData[-1], DltsConstants.DLTS_INT_BYTE_ORDER)

""" The `dltscontrol.dlts.ScanImage` class already implements the `dltscontrol.dlts.IScanImage` interface and supports 2D and 3D data. 
It creates the numpy array from a sequence of data points by converting each single datatpoint to the desired data to pick from the data point. """

class BitFlipRegisterAddressImage(ScanImage):
    """ 2D scan image which contains the register addresses. """

    _NAME = "Bit-Flip Registers"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IBitFlipScanDataPoint):
        return dataPoint.getFirstFlippedRegisterAddress()

class BitFlipRegistersCountImage(ScanImage):
    """ 2D scan image which contains the number of registers. """

    _NAME = "Number Of Bit-Flipped Registers"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IBitFlipScanDataPoint):
        return dataPoint.getNumberOfFlippedRegisters()

class BitFlipScan(Scan):
    """ The implemented bit-flip scan. """

    _NAME = "Bit-Flip Scan"

    def __init__(self, config, positioningTime_ms = 0, xTilt = None, zPosition = None, laserIntensity = None):
        super().__init__(config, positioningTime_ms, xTilt, zPosition, laserIntensity)

    def getName(self) -> str:
        return self._NAME

    def createScanImages(self, dataPoints):
        # create both scan images from the current data points
        return (BitFlipRegisterAddressImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
            self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()), 
            BitFlipRegistersCountImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
                self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()))

    def onScanStart(self, dltsConnection: DltsConnection):
        # send the scan start command
        dltsConnection.commandScanStart(BitFlipScanConstants.SCAN_START_COMMAND)

    def onScanAbort(self, dltsConnection: DltsConnection):
        # send the scan abort command
        dltsConnection.commandSkipUntilResponse(DltsCommand.ActionScanStop(), DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE)

    def onReceiveDataPoint(self, dltsConnection: DltsConnection):
        # receive the data point which consists of five bytes
        return BitFlipScanDataPoint(dltsConnection.read(BitFlipScanConstants.DATA_POINT_BYTE_COUNT))

""" Now that the scan and its data structures have been created it has be integrated into the application.

Scans are created using `dltscontrol.scanning.ScanCreationService`s. Those services are already in use and new ones can be added and created easily. Such
a service has to implement a single factory method which returns a fully configured scan. To get a fully configured scan we need to create the necessary
gui elements the user can interact with. Fortunately the most work is already done since the bit-flip scan doesn't need any special parameters.
"""

class BitFlipScanCreationService(ScanCreationService[BitFlipScan]):
    """ Scan creation service to create a `BitFlipScan`. """

    def createScan(self) -> BitFlipScan:
        # simply open a dialog in which the user can configure the bit-flip scan paramters and return the result afterwards
        return self.getContext().openDialog(BitFlipScanCreationDialog).waitForResult()

""" First we define an interface and implement a `dltscontrol.apptk.Panel` which allows the user to configure a bit-flip scan. The panel is then used 
in a dialog whose result will be a bit-flip scan. """ 

class BitFlipScanCreationPanel(StandardScanCreationPanel):
    """ Panel to create and configure a `BitFlipScan` (panel interface)
    
    The `StandardScanCreationPanel` already provides the interface for the default scan parameters and is based on a `ScanAreaConfigurationPanel`. Since 
    the bit-flip scan doesn't need more parameters than any standard scan the panel interface is already finished by deriving. 
    """
    def createScan(self) -> BitFlipScan:
        return BitFlipScan(self.getScanAreaConfigurationPanel().createAreaScanConfig(), self.getPositioningTime_ms(),
            self.getXTilt(), self.getZPosition(), self.getLaserIntensity())

class StandardBitFlipScanCreationPanel(StandardStandardScanCreationPanel, BitFlipScanCreationPanel):
    """ Default `BitFlipScanCreationPanel` implementation. 
    
    The `StandardStandardScanCreationPanel` implementation is totally sufficient. (No extra parameters)
    """
    pass

class BitFlipScanCreationDialog(ScanCreationDialog):
    """ Dialog which allows to create and configure a `BitFlipScan` based on a `BitFlipScanCreationPanel`. (dialog interface) The dialog interface 
    `ScanCreationDialog` already implements the ok-abort behavior we need. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> BitFlipScanCreationPanel:
        raise NotImplementedError 

class StandardBitFlipScanCreationDialog(BitFlipScanCreationDialog):
    """ Default `BitFlipScanCreationDialog` implementation defining the actual graphical appearance of the dialog. """

    _SCAN_PANEL_BORDER_WIDTH = 2
    _SCAN_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SCAN_PANEL_BORDER_PADX = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)
        # the constructors arguments should never be used

        # GUI creation and configuration is usually done in the constructor using tkinter of course

        # set the title of the actual dialog window on screen
        self.Window.title("Configure " + BitFlipScan._NAME)
        self.Window.resizable(False, False)

        # configure the scan creation panel cosmetics
        self.ScanCreationPanel.MainFrame.config(borderwidth = self._SCAN_PANEL_BORDER_WIDTH, relief = self._SCAN_PANEL_BORDER_RELIEF)

        # place the scan creation panel 
        self.ScanCreationPanel.getTk().pack(side = tk.TOP, padx = self._SCAN_PANEL_BORDER_PADX)

    def _createScanCreationPanel(self) -> BitFlipScanCreationPanel:
        return self.createPanel(BitFlipScanCreationPanel, self.getTk())

""" 
After all components have been implemented they have to get inserted into the application's manifest. Only actual instantiatable implementations can
be inserted. This should be done always at the end of a module so that it can be seen and modified easily. The new extenion has to be imported in the 
extenions.py file in order get integrated.
"""

from dltscontrol.app.manifest import manifest

# register the scan creation service with a proper scan name
manifest.insert(BitFlipScanCreationService, scanname = BitFlipScan._NAME)

# register the panel and dialog implementations
manifest.insert(StandardBitFlipScanCreationPanel)
manifest.insert(StandardBitFlipScanCreationDialog)