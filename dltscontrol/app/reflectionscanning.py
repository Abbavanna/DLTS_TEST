"""
Extension which adds a new `IScan`, the `ReflectionScan`, to the application with all his data structures to be possibly reused. Provides 
services, panels and dialogs to create such a scan.

Reuse
-----
You may implement the `IReflectionScanDataPoint` in your own custom `ScanDataPoint` to provide also a `ReflectionImage` in your own `IScanImage` implementation. 

Interfaces
----------
Panels: `ReflectionScanCreationPanel`.
Dialogs: `ReflectionScanCreationDialog`.

Implementations
---------------
Panels: `StandardReflectionScanCreationPanel`.
Dialogs: `StandardReflectionScanCreationDialog`.
Services: `ReflectionScanCreationService`.
"""
from dltscontrol.dlts import DltsConstants, DltsCommand, DltsConnection, IScanDataPoint, ScanDataPoint, ScanImage, Scan

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import OkAbortPanel, PaneledOkAbortDialog
from dltscontrol.app.scanning import StandardScanCreationPanel, StandardStandardScanCreationPanel, ScanCreationDialog, ScanCreationService
from dltscontrol.app.scanningconfigurables import ConfigurableStandardScanCreationDialog

class ReflectionScanConstants:

    DATA_POINT_BYTE_COUNT = 1

class IReflectionScanDataPoint(IScanDataPoint):
    """ A scan data point which holds a reflection value. """

    def getLaserReflection(self) -> int:
        raise NotImplementedError

class ReflectionScanDataPoint(ScanDataPoint, IReflectionScanDataPoint):
    """ The scan data point of a `ReflectionScan`. """

    def __init__(self, rawData):
        super().__init__(rawData)
    
    def getLaserReflection(self) -> int:
        return int.from_bytes(self.RawData, DltsConstants.DLTS_INT_BYTE_ORDER)

class ReflectionImage(ScanImage):
    """ A scan image which consists of the reflection values of `IReflectionScanDataPoint`s. """

    _NAME = "Laser Scanning Microscope"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate, scanDuration)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IReflectionScanDataPoint):
        return dataPoint.getLaserReflection()

class ReflectionScan(Scan):
    """ A scan which scans for laser reflections. Generates a `ReflectionScanImage`. """

    _NAME = "Laser Microscope Scan"

    def __init__(self, config, positioningTime_ms = 0, xTilt = None, zPosition = None, laserIntensity = None):
        super().__init__(config, positioningTime_ms, xTilt, zPosition, laserIntensity)

    def getName(self) -> str:
        return self._NAME

    def createScanImages(self, dataPoints):
        return (ReflectionImage(dataPoints, self.getAreaConfig().MinPosition, self.getAreaConfig().ScanImageSize, self.getAreaConfig().ScanResolution, 
            self.getLaserIntensity(), self.getZPosition(), self.getXTilt(), self.getStartTime(), self.getDuration()), )

    def onScanStart(self, dltsConnection: DltsConnection):
        dltsConnection.commandScanStart(DltsCommand.ActionScanArea())

    def onScanAbort(self, dltsConnection: DltsConnection):
        dltsConnection.commandSkipUntilResponse(DltsCommand.ActionScanStop(), DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE)

    def onReceiveDataPoint(self, dltsConnection: DltsConnection):
        return ReflectionScanDataPoint(dltsConnection.read(ReflectionScanConstants.DATA_POINT_BYTE_COUNT))

class ReflectionScanCreationService(ScanCreationService[ReflectionScan]):
    """ Scan creation service to create a `ReflectionScan`. """

    def createScan(self) -> ReflectionScan:
        return self.getContext().openDialog(ReflectionScanCreationDialog).waitForResult()

class ReflectionScanCreationPanel(StandardScanCreationPanel):
    """ Panel to create and configure a `ReflectionScan` """

    def createScan(self) -> ReflectionScan:
        return ReflectionScan(self.getScanAreaConfigurationPanel().createAreaScanConfig(), self.getPositioningTime_ms(),
            self.getXTilt(), self.getZPosition(), self.getLaserIntensity())

class StandardReflectionScanCreationPanel(StandardStandardScanCreationPanel, ReflectionScanCreationPanel):
    """ Default `ReflectionScanCreationPanel` implementation. """
    pass

class ReflectionScanCreationDialog(ScanCreationDialog):
    """ Dialog which allows to create and configure a `ReflectionScan` based on a `ReflectionScanCreationPanel`. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> ReflectionScanCreationPanel:
        raise NotImplementedError 

class StandardReflectionScanCreationDialog(ReflectionScanCreationDialog, ConfigurableStandardScanCreationDialog, PaneledOkAbortDialog):
    """ Default `ReflectionScanCreationDialog` implementation which uses user configured default values to fill in the 
    values of the scan creation panel. """

    _SCAN_PANEL_BORDER_WIDTH = 2
    _SCAN_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SCAN_PANEL_BORDER_PADX = 2

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure " + ReflectionScan._NAME)
        self.Window.resizable(False, False)

        self.ScanCreationPanel.MainFrame.config(borderwidth = self._SCAN_PANEL_BORDER_WIDTH, relief = self._SCAN_PANEL_BORDER_RELIEF)

        self.ScanCreationPanel.getTk().pack(side = tk.TOP, padx = self._SCAN_PANEL_BORDER_PADX)
        self.OkAbortPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)

    def _createScanCreationPanel(self) -> ReflectionScanCreationPanel:
        return self.createPanel(ReflectionScanCreationPanel, self.getTk())

    def _createOkAbortPanel(self) -> OkAbortPanel:
        return self.createPanel(OkAbortPanel, self.getTk())

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardReflectionScanCreationPanel)

# dialogs
manifest.insert(StandardReflectionScanCreationDialog)

# services
manifest.insert(ReflectionScanCreationService, scantype = ReflectionScan, scanname = ReflectionScan._NAME)