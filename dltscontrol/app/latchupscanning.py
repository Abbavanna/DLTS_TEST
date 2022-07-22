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

class LatchupScanConstants:

    DATA_POINT_BYTE_COUNT = 2

class ILatchupScanDataPoint(IScanDataPoint):
    """ A scan data point which holds a latchup current value. """

    def getLatchupCurrent(self) -> int:
        print("Not implemented")
        raise NotImplementedError

class LatchupImage(ScanImage):
    """ A scan image which consists of the latchup current values of `ILatchupScanDataPoint`s. """

    _NAME = "Single Event Latch-Ups"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: ILatchupScanDataPoint):
        return dataPoint.getLatchupCurrent()

class LatchupScanDataPoint(ScanDataPoint, ILatchupScanDataPoint):
    """ The scan data point of a `LatchupScan`. """

    def __init__(self, rawData):
        super().__init__(rawData)

    def getLatchupCurrent(self) -> int:
        print(" Got raw data :", self.RawData)
        return int.from_bytes(self.RawData, DltsConstants.DLTS_INT_BYTE_ORDER)

class LatchupScan(Scan):
    """ A scan which scans for latchup currents. Generates a `LatchupScanImage`. 
    
    Parameters
    ----------
    latchupTurnOffDelay_ms: `int` (default: `0`)
        The time after which to turn of the power supply to the scanned chip after a latchup has been detected.
    latchupTurnOffDelay_us: `int` (default: `0`)
        Has no effect and is not used anymore.
    """

    _NAME = "Single Event Latch-Up Scan"

    def __init__(self, config, latchupTurnOffDelay_ms = 0, positioningTime_ms = 0, xTilt = None, zPosition = None, laserIntensity = None):
        super().__init__(config, positioningTime_ms, xTilt, zPosition, laserIntensity)

        self._latchupTurnOffDelay_ms = latchupTurnOffDelay_ms

    @property
    def LatchupTurnOffDelay_ms(self) -> int:
        return self._latchupTurnOffDelay_ms
    
    def getName(self) -> str:
        return self._NAME

    def createScanImages(self, dataPoints):
        return (LatchupImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
            self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()), )

    def onScanStart(self, dltsConnection: DltsConnection):
        dltsConnection.commandSet(DltsCommand.SetLatchUpTurnOffDelayMilliseconds(self.LatchupTurnOffDelay_ms))
        dltsConnection.commandScanStart(DltsCommand.ActionScanLatchup())

    def onScanAbort(self, dltsConnection: DltsConnection):
        dltsConnection.commandSkipUntilResponse(DltsCommand.ActionScanStop(), DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE)

    def onReceiveDataPoint(self, dltsConnection: DltsConnection):
        return LatchupScanDataPoint(dltsConnection.read(LatchupScanConstants.DATA_POINT_BYTE_COUNT))

class LatchupScanCreationService(ScanCreationService[LatchupScan]):
    """ Scan creation service to create a `LatchupScan`. """

    def createScan(self) -> LatchupScan:
        return self.getContext().openDialog(LatchupScanCreationDialog).waitForResult()

class LatchupScanCreationPanel(StandardScanCreationPanel):
    """ Panel to create and configure a `LatchupScan` """

    def getLatchupTurnOffDelayMilliseconds(self) -> int:
        raise NotImplementedError

    def setLatchupTurnOffDelayMilliseconds(self, turnOffDelay_ms: int):
        raise NotImplementedError

    def createScan(self) -> LatchupScan:
        return LatchupScan(self.getScanAreaConfigurationPanel().createAreaScanConfig(), self.getLatchupTurnOffDelayMilliseconds(), 
            self.getPositioningTime_ms(), self.getXTilt(), self.getZPosition(), self.getLaserIntensity())

class VariabledLatchupScanCreationPanel(VariabledStandardScanCreationPanel, LatchupScanCreationPanel):
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

class StandardLatchupScanCreationPanel(StandardStandardScanCreationPanel, VariabledLatchupScanCreationPanel, LatchupScanCreationPanel):
    """ Default `LatchupScanCreationPanel` implementation. """
    
    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        latchupTimesFrame = ttk.Frame(self.getTk())

        latchupTimesLabel = ttk.Label(latchupTimesFrame, text = "Latchup Turn Off Delay [ms]")
        millisEntry = tkext.IntEntry(latchupTimesFrame, width = self._ENTRY_WIDTH, textvariable = self.LatchupTurnOffDelayMillisecondsVariable)

        millisEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)
        latchupTimesLabel.pack(side = tk.RIGHT)

        latchupTimesFrame.pack(side = tk.TOP, fill = tk.X, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY)

class LatchupScanCreationDialog(ScanCreationDialog):
    """ Dialog which allows to create and configure a `LatchupScan` based on a `LatchupScanCreationPanel`. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> LatchupScanCreationPanel:
        raise NotImplementedError

class StandardLatchupScanCreationDialog(LatchupScanCreationDialog, ConfigurableStandardScanCreationDialog, PaneledOkAbortDialog):
    """ Default `LatchupScanCreationDialog` implementation which uses user configured default values to fill in the 
    values of the scan creation panel. """

    _LATCHUP_USER_CONFIG_SECTION = "Latchup Scan Dialog"

    _LATCHUP_TURN_OFF_DELAY_MS = "turnoffdelay-ms"
    _LATCHUP_TURN_OFF_DELAY_MS_DEFAULT = 1

    _SCAN_PANEL_BORDER_WIDTH = 2
    _SCAN_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SCAN_PANEL_BORDER_PADX = 2

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure " + LatchupScan._NAME)
        self.Window.resizable(False, False)

        self.ScanCreationPanel.MainFrame.config(borderwidth = self._SCAN_PANEL_BORDER_WIDTH, relief = self._SCAN_PANEL_BORDER_RELIEF)

        self.ScanCreationPanel.MainFrame.pack(side = tk.TOP, padx = self._SCAN_PANEL_BORDER_PADX)
        self.OkAbortPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)

    def _createScanCreationPanel(self) -> LatchupScanCreationPanel:
        return self.createPanel(LatchupScanCreationPanel, self.getTk())

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
manifest.insert(StandardLatchupScanCreationPanel)

# dialogs
manifest.insert(StandardLatchupScanCreationDialog)

# services
manifest.insert(LatchupScanCreationService, scantype = LatchupScan, scanname = LatchupScan._NAME)