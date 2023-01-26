"""
Extension which adds a new `Multi Intensity Scan`, to the application with all his data structures to be possibly reused. Provides
panels, dialogs and services to create such a scan.

MI = MULTI INTENSITY

Interfaces
----------
Panels: `MIScanCreationPanel`.
Dialogs: `MIScanCreationDialog`.

Implementations
---------------
Panels: `StandardMIScanCreationPanel`.
Dialogs: `StandardMIScanCreationDialog`.
Services: `MIScanCreationService`.
"""

from dltscontrol.dlts import DltsConstants, DltsCommand, DltsConnection, IScanDataPoint, ScanDataPoint, Scan, ScanImage

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import OkAbortPanel, PaneledOkAbortDialog, IUserConfig
from dltscontrol.app.scanning import (
    StandardScanCreationPanel,
    StandardStandardScanCreationPanel,
    VariabledStandardScanCreationPanel,
    ScanCreationDialog,
    ScanCreationService,
    StandardMultiIntScanCreationPanel
)
from dltscontrol.app.scanningconfigurables import ConfigurableStandardScanCreationDialog


class MIScanConstants:
    """ Constants for the Multi Intensity scan and related classes. """

    DATA_POINT_BYTE_COUNT = 8   #  The number of bytes in a data point of a multi intensity scan.
    SCAN_START_COMMAND = str.encode("asn") # The command to start a multi intensity scan.


class IMIScanDataPoint(IScanDataPoint):
    """ A scan data point which holds a latchup current,reflectivity and voltage value. """

    def getLatchUpCurrent(self) -> int:
        """ The first two bytes contain the latch up current. """
        raise NotImplementedError

    def getReflectionValue(self) -> int:
        """ the last byte contains the reflection value. """
        raise NotImplementedError

    def getLatchUpVoltage(self) -> int:
        """ the last byte contains the voltage value. """
        raise NotImplementedError




class MILatchupImage(ScanImage):
    """ A scan image which consists of the latchup current values of `IMIScanDataPoint`s. """

    _NAME = "Latch-Up Current Image"

    def __init__(self,
                 dataPoints,
                 position,
                 size,
                 resolution,
                 laserIntensity,
                 zPosition,
                 xTilt,
                 scanDate,
                 scanDuration,
                 intensity_multiplier):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate,
                         scanDuration, intensity_multiplier)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IMIScanDataPoint):
        return dataPoint.getLatchUpCurrent()

    @staticmethod
    def detect_latchup_condition(data):
        # TODO: latchup condition here. Keep this if you want to have latchup check in python instead of in msp430 file
        #  ( current > 13 ma or voltage < 100)
        # temp_return_value = [test for test in data if test > 13]
        # data_len = len(temp_return_value) if len(temp_return_value) > 0 else 1
        # return_value = int(sum(temp_return_value) / data_len)
        # return return_value
        return int(sum(data) / len(data))



class MILaserImage(ScanImage):
    """ A scan image which consists of the threshold intensity values of `IMIScanDataPoint`s. """

    _NAME = "Laser Intensity"

    def __init__(self,
                 dataPoints,
                 position,
                 size,
                 resolution,
                 laserIntensity,
                 zPosition,
                 xTilt,
                 scanDate,
                 scanDuration,
                 intensity_multiplier):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate,
                         scanDuration, intensity_multiplier)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IMIScanDataPoint):
        return dataPoint.getLaserValue()

    @staticmethod
    def detect_latchup_condition(data):
        return int(sum(data) / len(data))


class MIReflectionImage(ScanImage):
    """ A scan image which consists of the reflectivity values of `IMIScanDataPoint`s """

    _NAME = "Reflection Scan Image"

    def __init__(self, dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate,
                 scanDuration, intensity_multiplier):
        super().__init__(dataPoints, position, size, resolution, laserIntensity, zPosition, xTilt, scanDate,
                         scanDuration, intensity_multiplier)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IMIScanDataPoint):
        return dataPoint.getReflectionValue()
    #
    @staticmethod
    def detect_latchup_condition(data):
        return int(sum(data) / len(data))


class MIVoltageImage(ScanImage):
    """ A scan image which consists of the voltage values of `IMIScanDataPoint`s """

    _NAME = "Voltage Scan Image"

    def __init__(self,
                 dataPoints,
                 position,
                 size,
                 resolution,
                 laserIntensity,
                 zPosition,
                 xTilt,
                 scanDate,
                 scanDuration,
                 intensity_multiplier):
        super().__init__(dataPoints,
                         position,
                         size,
                         resolution,
                         laserIntensity,
                         zPosition,
                         xTilt,
                         scanDate,
                         scanDuration,
                         intensity_multiplier)

    def getName(self) -> str:
        return self._NAME

    def convertDataPoint(self, dataPoint: IMIScanDataPoint):
        return dataPoint.getLatchUpVoltage()

    @staticmethod
    def detect_latchup_condition(data):
        # TODO: latchup condition here. Keep this if you want to have latchup check in python instead of in msp430 file
        #  ( current > 13 ma or voltage < 100)
        # temp_return_value = [test for test in data if test < 100]
        # data_len = len(temp_return_value) if len(temp_return_value) > 0 else 1
        # return_value = int(sum(temp_return_value) / data_len)
        # return return_value

        return int(sum(data) / len(data))






class MIScanDataPoint(ScanDataPoint, IMIScanDataPoint):
    """ The scan data point of a `Multi Intensity Scan`. """

    def __init__(self, rawData):
        super().__init__(rawData)

    def getReflectionValue(self):
        return int.from_bytes(self.RawData[-8:-6], DltsConstants.DLTS_INT_BYTE_ORDER)

    def getLaserValue(self):
        return int.from_bytes(self.RawData[-6:-4], DltsConstants.DLTS_INT_BYTE_ORDER)

    def getLatchUpCurrent(self):
        return int.from_bytes(self.RawData[-4:-2], DltsConstants.DLTS_INT_BYTE_ORDER)

    def getLatchUpVoltage(self):
        return int.from_bytes(self.RawData[-2:], DltsConstants.DLTS_INT_BYTE_ORDER)


    def debug_get_all_as_list(self): #Return all the raw data as a list
        return list(self.RawData)


class MIScan(Scan):
    """ A scan which scans for latchup currents,voltages,intensities and reflectivity values. Generates a `MIScanImage`.
    """

    _NAME = "Multi Intensity Scan"

    def __init__(self,
                 config,
                 latchupTurnOffDelay_ms=0,
                 positioningTime_ms=0,
                 xTilt=None,
                 zPosition=None,
                 laserIntensity=None,
                 autoFocus=None,
                 laserMinIntensity=None,
                 laserMaxIntensity=None,
                 laserStepIntensity=None,
                 ):
        super().__init__(
            config,
            positioningTime_ms,
            xTilt,
            zPosition,
            laserIntensity,
            autoFocus,
            laserMinIntensity,
            laserMaxIntensity,
            laserStepIntensity
        )

        self._latchupTurnOffDelay_ms = latchupTurnOffDelay_ms

    @property
    def LatchupTurnOffDelay_ms(self) -> int:
        return self._latchupTurnOffDelay_ms

    def getName(self) -> str:
        return self._NAME

    def createScanImages(self, dataPoints):


        return (MILatchupImage(dataPoints,
                               self.getAreaConfig().MinPosition,
                               self.getAreaConfig().ScanImageSize,
                               self.getAreaConfig().ScanResolution,
                               self.getLaserIntensity(),
                               self.getZPosition(),
                               self.getXTilt(),
                               self.getStartTime(),
                               self.getDuration(),
                               self.getAreaConfig().IntensityMultiplier
                               ),
                MILaserImage(dataPoints,
                               self.getAreaConfig().MinPosition,
                               self.getAreaConfig().ScanImageSize,
                               self.getAreaConfig().ScanResolution,
                               self.getLaserIntensity(),
                               self.getZPosition(),
                               self.getXTilt(),
                               self.getStartTime(),
                               self.getDuration(),
                               self.getAreaConfig().IntensityMultiplier
                               ),
                MIReflectionImage(dataPoints,
                                  self.getAreaConfig().MinPosition,
                                  self.getAreaConfig().ScanImageSize,
                                  self.getAreaConfig().ScanResolution,
                                  self.getLaserIntensity(),
                                  self.getZPosition(),
                                  self.getXTilt(),
                                  self.getStartTime(),
                                  self.getDuration(),
                                  self.getAreaConfig().IntensityMultiplier),
                MIVoltageImage(dataPoints,
                               self.getAreaConfig().MinPosition,
                               self.getAreaConfig().ScanImageSize,
                               self.getAreaConfig().ScanResolution,
                               self.getLaserIntensity(),
                               self.getZPosition(),
                               self.getXTilt(),
                               self.getStartTime(),
                               self.getDuration(),
                               self.getAreaConfig().IntensityMultiplier)
                )

    def onScanStart(self, dltsConnection: DltsConnection):
        dltsConnection.commandSet(DltsCommand.SetLatchUpTurnOffDelayMilliseconds(self.LatchupTurnOffDelay_ms))
        dltsConnection.commandScanStart(MIScanConstants.SCAN_START_COMMAND)

    def setAutoFocus(self, dltsConnection: DltsConnection):
        # send an autofocus command to the DLTS
        dltsConnection.commandDataRetrieval(
            DltsCommand.ActionScanAutoFocus(), DltsConstants.DLTS_AUTOFOCUS_RESPONSE_LENGTH) #TODO: focus

    def setScanLaserMinIntensity(self, dltsConnection: DltsConnection, value):
        # send Laser Minimum Intensity Value to the DLTS
        dltsConnection.commandSet(DltsCommand.SetLaserMinIntensity(value))

    def setScanLaserMaxIntensity(self, dltsConnection: DltsConnection, value):
        # send Laser Minimum Intensity Value to the DLTS
        dltsConnection.commandSet(DltsCommand.SetLaserMaxIntensity(value))

    def setScanLaserStepIntensity(self, dltsConnection: DltsConnection, value):
        # send Laser Intensity Step Value to the DLTS
        dltsConnection.commandSet(DltsCommand.SetLaserIntensityStep(value))

    def onScanAbort(self, dltsConnection: DltsConnection):
        dltsConnection.commandSkipUntilResponse(DltsCommand.ActionScanStop(), DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE)

    def onReceiveDataPoint(self, dltsConnection: DltsConnection):
        return MIScanDataPoint(dltsConnection.read(MIScanConstants.DATA_POINT_BYTE_COUNT))


class MIScanCreationService(ScanCreationService[MIScan]):
    """ Scan creation service to create a `Multi Intensity Scan`. """

    def createScan(self) -> MIScan:
        return self.getContext().openDialog(MIScanCreationDialog).waitForResult()


class MIScanCreationPanel(StandardScanCreationPanel):
    """ Panel to create and configure a `Multi Intensity Scan` """

    def getLatchupTurnOffDelayMilliseconds(self) -> int:
        raise NotImplementedError

    def setLatchupTurnOffDelayMilliseconds(self, turnOffDelay_ms: int):
        raise NotImplementedError

    def createScan(self) -> MIScan:

        # To create scan images for all intensities given, multiply the number of intensity to determine the data points.
        import math
        intensity_multiplier = math.floor(
            (self.getLaserMaxIntensity() - self.getLaserMinIntensity())+ self.getLaserStepIntensity()) + 1

        return MIScan(
            self.getScanAreaConfigurationPanel().createAreaScanConfig(intensity_multiplier),
            self.getLatchupTurnOffDelayMilliseconds(),
            self.getPositioningTime_ms(),
            self.getXTilt(),
            self.getZPosition(),
            self.getLaserIntensity(),
            self.getAutoFocusVariable(),
            self.getLaserMinIntensity(),
            self.getLaserMaxIntensity(),
            self.getLaserStepIntensity()
        )


class VariabledMIScanCreationPanel(VariabledStandardScanCreationPanel, MIScanCreationPanel):
    """ A `MIScanCreationPanel` whose values are stored in tkinter variables. """

    _DEFAULT_LATCHUP_TURN_OFF_MILLISECONDS = 1

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._latchupTurnOffMilliVar = tkext.IntNoneVar(self.getTk(), self._DEFAULT_LATCHUP_TURN_OFF_MILLISECONDS)

        self._autoFocusVariable = tk.IntVar()
        self._autoFocusVariable.set(0)  # Initializes the value to "unset"

    @property
    def autoFocusVariable(self):
        return self._autoFocusVariable

    def getAutoFocusVariable(self):
        return self._autoFocusVariable.get()

    def setAutoFocusVariable(self, value):
        self._autoFocusVariable.set(value)

    @property
    def LatchupTurnOffDelayMillisecondsVariable(self) -> tkext.IntNoneVar:
        return self._latchupTurnOffMilliVar

    def getLatchupTurnOffDelayMilliseconds(self) -> int:
        return self._latchupTurnOffMilliVar.get()

    def setLatchupTurnOffDelayMilliseconds(self, turnOffDelay_ms: int):
        self._latchupTurnOffMilliVar.set(turnOffDelay_ms)


class StandardMIScanCreationPanel(StandardMultiIntScanCreationPanel,
                                  VariabledMIScanCreationPanel,
                                  MIScanCreationPanel):
    """ Default `MIScanCreationPanel` implementation. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        latchupTimesFrame = ttk.Frame(self.getTk())

        autoFocusButton = ttk.Checkbutton(latchupTimesFrame,
                                          text="Auto Focus",
                                          width=15,
                                          variable=self.autoFocusVariable)

        latchupTimesLabel = ttk.Label(latchupTimesFrame, text="Latchup Turn Off Delay [ms]")
        millisEntry = tkext.IntEntry(latchupTimesFrame, width=self._ENTRY_WIDTH,
                                     textvariable=self.LatchupTurnOffDelayMillisecondsVariable)

        millisEntry.pack(side=tk.RIGHT, padx=self._ENTRY_PADX)
        latchupTimesLabel.pack(side=tk.RIGHT)

        autoFocusButton.pack(side=tk.RIGHT, padx=15, pady=2)
        latchupTimesFrame.pack(side=tk.TOP, fill=tk.X, padx=self._VARIABLE_PADX, pady=self._VARIABLE_PADY)


class MIScanCreationDialog(ScanCreationDialog):
    """ Dialog which allows to create and configure a `LatchupScan` based on a `LatchupScanCreationPanel`. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> MIScanCreationPanel:
        raise NotImplementedError


class StandardMIScanCreationDialog(MIScanCreationDialog, ConfigurableStandardScanCreationDialog, PaneledOkAbortDialog):
    """ Default `MIScanCreationDialog` implementation which uses user configured default values to fill in the
    values of the scan creation panel. """

    _LATCHUP_USER_CONFIG_SECTION = "Multi Intensity Scan Dialog"

    _LATCHUP_TURN_OFF_DELAY_MS = "turnoffdelay-ms"
    _LATCHUP_TURN_OFF_DELAY_MS_DEFAULT = 1

    _SCAN_PANEL_BORDER_WIDTH = 2
    _SCAN_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SCAN_PANEL_BORDER_PADX = 2

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure " + MIScan._NAME)
        self.Window.resizable(False, False)

        self.ScanCreationPanel.MainFrame.config(borderwidth=self._SCAN_PANEL_BORDER_WIDTH,
                                                relief=self._SCAN_PANEL_BORDER_RELIEF)

        self.ScanCreationPanel.MainFrame.pack(side=tk.TOP, padx=self._SCAN_PANEL_BORDER_PADX)
        self.OkAbortPanel.getTk().pack(side=tk.TOP, pady=self._PANEL_PADY)

    def _createScanCreationPanel(self) -> MIScanCreationPanel:
        return self.createPanel(MIScanCreationPanel, self.getTk())

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

        turnOffDelay_ms = int(userConfig.getSet(self._LATCHUP_USER_CONFIG_SECTION, self._LATCHUP_TURN_OFF_DELAY_MS,
                                                self._LATCHUP_TURN_OFF_DELAY_MS_DEFAULT))
        self.ScanCreationPanel.setLatchupTurnOffDelayMilliseconds(turnOffDelay_ms)

    def _saveConfigValues(self, userConfig):
        super()._saveConfigValues(userConfig)

        userConfig.set(self._LATCHUP_USER_CONFIG_SECTION, self._LATCHUP_TURN_OFF_DELAY_MS,
                       self.ScanCreationPanel.getLatchupTurnOffDelayMilliseconds())


# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardMIScanCreationPanel)

# dialogs
manifest.insert(StandardMIScanCreationDialog)

# services
manifest.insert(MIScanCreationService, scantype=MIScan, scanname=MIScan._NAME)
