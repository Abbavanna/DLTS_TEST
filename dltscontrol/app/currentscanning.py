"""
Extension which adds a new `IScan`, the `LatchupScan`, to the application with all his data structures to be possibly reused. Provides 
panels, dialogs and services to create such a scan.

Reuse
-----
You may implement the `ILatchupScanDataPoint` in your own custom `ScanDataPoint` to provide also a `LatchupImage` in your own `IScanImage` implementation. 

Interfaces
----------
Panels: `LatchupScanCreationPanel`.
Dialogs: `LatchupScanCreationDialog`.

Implementations
---------------
Panels: `StandardLatchupScanCreationPanel`.
Dialogs: `StandardLatchupScanCreationDialog`.
Services: `LatchupScanCreationService`.
"""
from dltscontrol.dlts import DltsConstants, DltsCommand, DltsConnection, IScanDataPoint, ScanDataPoint, Scan, ScanImage

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import OkAbortPanel, PaneledOkAbortDialog, IUserConfig
from dltscontrol.app.scanning import StandardScanCreationPanel, StandardStandardScanCreationPanel, \
    VariabledStandardScanCreationPanel, ScanCreationDialog, ScanCreationService
from dltscontrol.app.scanningconfigurables import ConfigurableStandardScanCreationDialog

class CurrentScanConstants:

    DATA_POINT_BYTE_COUNT = 6
    SCAN_START_COMMAND = str.encode("asc") # action scan multi

class ICurrentScanDataPoint(IScanDataPoint):
    """ A scan data point which holds a latchup current value. """

    def getLatchUpCurrent(self) -> int:
        """ The first two bytes contain the latch up current. """
        raise NotImplementedError

    def getReflectionValue(self) -> int:
        """ the last byte contains the reflection value. """
        raise NotImplementedError
        
    def getBaseCurrent(self) -> int:
        """ the last byte contains the reflection value. """
        raise NotImplementedError

class CurrentLatchUpImage(ScanImage):
    """ 2D scan image which contains the latch-up currents """

    _NAME = "Latch-Up Current Image"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: ICurrentScanDataPoint):
        return dataPoint.getLatchUpCurrent()

class CurrentReflectionImage(ScanImage):
    """ 2D scan image which contains the number of registers. """

    _NAME = "Reflection Scan Image"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: ICurrentScanDataPoint):
        return dataPoint.getReflectionValue()
        
class BaseCurrentImage(ScanImage):
    """ 2D scan image which contains the number of registers. """

    _NAME = "Base Current Image"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: ICurrentScanDataPoint):
        return dataPoint.getBaseCurrent()

class CurrentScanDataPoint(ScanDataPoint, ICurrentScanDataPoint):
    """ The scan data point of a `CurrentScan`. """

    def __init__(self, rawData):
        super().__init__(rawData)

    def getBaseCurrent(self):
        return int.from_bytes(self.RawData[-2:], DltsConstants.DLTS_INT_BYTE_ORDER) #selecting array elements in python: [start:stop:step length]#negative values are used as [array length - value]

    def getLatchUpCurrent(self):
        return int.from_bytes(self.RawData[-4:-2], DltsConstants.DLTS_INT_BYTE_ORDER) 																				
																					
    def getReflectionValue(self):
        return int.from_bytes(self.RawData[-6:-4], DltsConstants.DLTS_INT_BYTE_ORDER)

class CurrentScan(Scan):
    """ A scan which scans for latchup currents. Generates a `LatchupScanImage`. 
    
    Parameters
    ----------
    latchupTurnOffDelay_ms: `int` (default: `0`)
        The time after which to turn of the power supply to the scanned chip after a latchup has been detected.
    latchupTurnOffDelay_us: `int` (default: `0`)
        Has no effect and is not used anymore.
    """

    _NAME = "Current Scan"

    def __init__(self, config, latchupTurnOffDelay_ms = 0, positioningTime_ms = 0, xTilt = None, zPosition = None, laserIntensity = None):
        super().__init__(config, positioningTime_ms, xTilt, zPosition, laserIntensity)

        self._latchupTurnOffDelay_ms = latchupTurnOffDelay_ms

    @property
    def LatchupTurnOffDelay_ms(self) -> int:
        return self._latchupTurnOffDelay_ms
    
    def getName(self) -> str:
        return self._NAME

    def createScanImages(self, dataPoints):
        # create three scan images from the current data points
        return (CurrentLatchUpImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
        self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()), 
		CurrentReflectionImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
		self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()),
		BaseCurrentImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
		self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration())
		)

    def onScanStart(self, dltsConnection: DltsConnection):
        # send the scan start command
        dltsConnection.commandScanStart(CurrentScanConstants.SCAN_START_COMMAND)

    def onScanAbort(self, dltsConnection: DltsConnection):
        # send the scan abort command
        dltsConnection.commandSkipUntilResponse(DltsCommand.ActionScanStop(), DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE)

    def onReceiveDataPoint(self, dltsConnection: DltsConnection):
        # receive the data point which consists of five bytes
        return CurrentScanDataPoint(dltsConnection.read(CurrentScanConstants.DATA_POINT_BYTE_COUNT))

class CurrentScanCreationService(ScanCreationService[CurrentScan]):
    """ Scan creation service to create a `LatchupScan`. """

    def createScan(self) -> CurrentScan:
        return self.getContext().openDialog(CurrentScanCreationDialog).waitForResult()

class CurrentScanCreationPanel(StandardScanCreationPanel):
    """ Panel to create and configure a `LatchupScan` """

    def getLatchupTurnOffDelayMilliseconds(self) -> int:
        raise NotImplementedError

    def setLatchupTurnOffDelayMilliseconds(self, turnOffDelay_ms: int):
        raise NotImplementedError

    def createScan(self) -> CurrentScan:
        return CurrentScan(self.getScanAreaConfigurationPanel().createAreaScanConfig(), self.getLatchupTurnOffDelayMilliseconds(),
            self.getPositioningTime_ms(), self.getXTilt(), self.getZPosition(), self.getLaserIntensity())

class VariabledCurrentScanCreationPanel(VariabledStandardScanCreationPanel, CurrentScanCreationPanel):
    """ A `LatchupScanCreationPanel` whose values are stored in tkinter variables. """
    
    _DEFAULT_LATCHUP_TURN_OFF_MILLISECONDS = 1

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._latchupTurnOffMilliVar = tkext.IntNoneVar(self.getTk(), self._DEFAULT_LATCHUP_TURN_OFF_MILLISECONDS)

    @property
    def LatchupTurnOffDelayMillisecondsVariable(self) -> tkext.IntNoneVar:
        return self._latchupTurnOffMilliVar

    def getLatchupTurnOffDelayMilliseconds(self) -> int:
        return self._latchupTurnOffMilliVar.get()

    def setLatchupTurnOffDelayMilliseconds(self, turnOffDelay_ms: int):
        self._latchupTurnOffMilliVar.set(turnOffDelay_ms)

class StandardCurrentScanCreationPanel(StandardStandardScanCreationPanel, VariabledCurrentScanCreationPanel, CurrentScanCreationPanel):
    """ Default `LatchupScanCreationPanel` implementation. """
    
    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        latchupTimesFrame = ttk.Frame(self.getTk())

        latchupTimesLabel = ttk.Label(latchupTimesFrame, text = "Latchup Turn Off Delay [ms]")
        millisEntry = tkext.IntEntry(latchupTimesFrame, width = self._ENTRY_WIDTH, textvariable = self.LatchupTurnOffDelayMillisecondsVariable)

        millisEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)
        latchupTimesLabel.pack(side = tk.RIGHT)

        latchupTimesFrame.pack(side = tk.TOP, fill = tk.X, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY)

class CurrentScanCreationDialog(ScanCreationDialog):
    """ Dialog which allows to create and configure a `LatchupScan` based on a `LatchupScanCreationPanel`. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> CurrentScanCreationPanel:
        raise NotImplementedError

class StandardCurrentScanCreationDialog(CurrentScanCreationDialog, ConfigurableStandardScanCreationDialog, PaneledOkAbortDialog):
    """ Default `LatchupScanCreationDialog` implementation which uses user configured default values to fill in the 
    values of the scan creation panel. """

    _LATCHUP_USER_CONFIG_SECTION = "Current Scan Dialog"

    _LATCHUP_TURN_OFF_DELAY_MS = "turnoffdelay-ms"
    _LATCHUP_TURN_OFF_DELAY_MS_DEFAULT = 1

    _SCAN_PANEL_BORDER_WIDTH = 2
    _SCAN_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SCAN_PANEL_BORDER_PADX = 2

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure " + CurrentScan._NAME)
        self.Window.resizable(False, False)

        self.ScanCreationPanel.MainFrame.config(borderwidth = self._SCAN_PANEL_BORDER_WIDTH, relief = self._SCAN_PANEL_BORDER_RELIEF)

        self.ScanCreationPanel.MainFrame.pack(side = tk.TOP, padx = self._SCAN_PANEL_BORDER_PADX)
        self.OkAbortPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)

    def _createScanCreationPanel(self) -> CurrentScanCreationPanel:
        return self.createPanel(CurrentScanCreationPanel, self.getTk())

    def _createOkAbortPanel(self) -> OkAbortPanel:
        return self.createPanel(OkAbortPanel, self.getTk())

    def saveConfigToDict(self, values):
        super().saveConfigToDict(values)

        values[self._LATCHUP_TURN_OFF_DELAY_MS] = self.ScanCreationPanel.getLatchupTurnOffDelayMilliseconds()

    def loadConfigFromDict(self, values):
        super().loadConfigFromDict(values)

        self.ScanCreationPanel.setLatchupTurnOffDelayMilliseconds(values.get(self._LATCHUP_TURN_OFF_DELAY_MS, 
            self.ScanCreationPanel.getLatchupTurnOffDelayMilliseconds()))

    def _loadConfigValues(self, userConfig: IUserConfig):
        super()._loadConfigValues(userConfig)

        turnOffDelay_ms = int(userConfig.getSet(self._LATCHUP_USER_CONFIG_SECTION, self._LATCHUP_TURN_OFF_DELAY_MS, self._LATCHUP_TURN_OFF_DELAY_MS_DEFAULT))
        self.ScanCreationPanel.setLatchupTurnOffDelayMilliseconds(turnOffDelay_ms)  

    def _saveConfigValues(self, userConfig):
        super()._saveConfigValues(userConfig)

        userConfig.set(self._LATCHUP_USER_CONFIG_SECTION, self._LATCHUP_TURN_OFF_DELAY_MS, self.ScanCreationPanel.getLatchupTurnOffDelayMilliseconds())

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardCurrentScanCreationPanel)

# dialogs
manifest.insert(StandardCurrentScanCreationDialog)

# services
manifest.insert(CurrentScanCreationService, scantype = CurrentScan, scanname = CurrentScan._NAME)
