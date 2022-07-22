""" 
Extension which provides service, panel and dialog interfaces and templates for scan creation. 

Inherit from any suitable class to create custom scan configuration and creation panels, dialogs and services.

Interfaces
----------
Panels: `ScanAreaConfiguarationPanel` and `ScanProgressPanel`.
Services: `ScanCreationService`.

`ScanCreationPanel` and `StandardScanCreationPanel` aren't real useable panel interfaces since they don't specifiy the final scan type to create.
Although, they may be subject of custom implementations.

Additional Derivables
---------------------
Panels: `VariabledScanAreaConfigurationPanel`, `VariabledStandardScanCreationPanel` and `StandardStandardScanCreationPanel`.
Components: `IScanCreationComponent`. Use this if you need to interact with `ScanCreationService`s since it provides a much more convenient 
way to interact than directly dealing with the services and context.

Implementations
---------------
Panels: `StandardScanAreaConfiguarationPanel` and `StandardScanProgressPanel`.
"""
from typing import List, Tuple, Type, TypeVar, Generic, Union

from dltscontrol.apptk import IComponent, Service, Panel, showerror
from dltscontrol.dlts import IScan, Scan, ScanAreaConfig

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import rootLogger, IDltsComponent, OkAbortDialog

logger = rootLogger.getChild(__name__)

SCAN_TYPE_KEY = "scantype"
SCAN_NAME_KEY = "scanname"

TScan = TypeVar("TScan", bound = IScan)

class ScanCreationService(Service, Generic[TScan]):
    """ Service interface which allows factory like scan creations. 
    
    Manifest Properties
    -------------------
    scantype: `Type`
        The type of the scan which can be created. For instance: `scantype = ReflectionScan`.
    scanname:
        The name of the scan which can be created. For instance: `scanname = "Reflection Scan"`.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def createScan(self) -> TScan:
        """ Creates and returns a new scan. """
        raise NotImplementedError

class IScanCreationComponent(IComponent):
    """ Helper component which provides convenient methods to interact with `ScanCreationService`s. """

    def requestScanCreationService(self, scanName: str = None, scanType: Type[TScan] = None, serviceName: str = None) -> ScanCreationService:
        """ Requests a scan creation service which has been registered under the specified properties. 
        
        Parameters
        ----------
        scanName: `str` (default: `None`)
            The scanname under which the scan creation service must have been registered. If `None` it's ignored.
        scanType: `Type[TScan]` (default: `None`)
            The scantype under which the scan creation service must have been registered. If `None` it's ignored.
        serviceName: `str` (default: `None`)
            The name under which the scan creation service must have been registered. If `None` it's ignored.

        Returns
        -------
        scanCreationService: ScanCreationService
            The requested scan creation service.
        """
        return self.getComponentContext().requestService(next(iter(self.getScanCreationServiceClasses(scanName, scanType, serviceName)), None))

    def getScanNames(self) -> Tuple[str]:
        """ Returns the scannames of all registered scan creation services. """
        return tuple(map(lambda serviceClass: self.getScanName(serviceClass), self.getScanCreationServiceClasses()))

    def getScanType(self, scanCreationServiceClass: Type) -> Union[Type[TScan], type(None)]:
        """ Returns the scantype under which the specified scan creation service class has been registered. """
        return self.getContext().Application.Manifest.getProperties(scanCreationServiceClass).get(SCAN_TYPE_KEY, None)

    def getScanName(self, scanCreationServiceClass: Type) -> Union[str, type(None)]:
        """ Returns the scanname under which the specified scan creation service class has been registered. """
        return self.getContext().Application.Manifest.getProperties(scanCreationServiceClass).get(SCAN_NAME_KEY, None)

    def getScanCreationServiceClasses(self, scanName: str = None, scanType: Type[TScan] = None, serviceName: str = None) -> List[Type]:
        """ Returns all scan creation service classes which are registered under the specified properties. 
        
        Parameters
        ----------
        scanName: `str` (default: `None`)
            The scanname under which the scan creation service must have been registered. If `None` it's ignored.
        scanType: `Type[TScan]` (default: `None`)
            The scantype under which the scan creation service must have been registered. If `None` it's ignored.
        serviceName: `str` (default: `None`)
            The name under which the scan creation service must have been registered. If `None` it's ignored.

        Returns
        -------
        scanCreationServiceClasses: List[Type]
            The scan creation service classes.
        """
        scanCreationServiceClasses = list()

        for serviceClass in self.getContext().Application.Manifest.getComponentClasses(ScanCreationService, serviceName):
            serviceScanName = self.getScanName(serviceClass)
            serviceScanType = self.getScanType(serviceClass)

            if scanName and (not serviceScanName or scanName != serviceScanName):
                continue

            if scanType and (not serviceScanType or not issubclass(serviceScanType, scanType)):
                continue

            scanCreationServiceClasses.append(serviceClass)
        
        return scanCreationServiceClasses

class ScanAreaConfiguarationPanel(Panel):
    """ Panel interface to configure and create `ScanAreaConfig`. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def getXBoundsLow(self) -> int:
        raise NotImplementedError

    def setXBoundsLow(self, xBoundsLow: int):
        raise NotImplementedError

    def getXBoundsHigh(self) -> int:
        raise NotImplementedError

    def setXBoundsHigh(self, xBoundsHigh: int):
        raise NotImplementedError

    def getXStepSize(self) -> int:
        raise NotImplementedError

    def setXStepSize(self, xStepSize: int):
        raise NotImplementedError

    def getXDelay_ms(self) -> int:
        raise NotImplementedError

    def setXDelay_ms(self, xDelay_ms: int):
        raise NotImplementedError

    def getYBoundsLow(self) -> int:
        raise NotImplementedError

    def setYBoundsLow(self, yBoundsLow: int):
        raise NotImplementedError

    def getYBoundsHigh(self) -> int:
        raise NotImplementedError

    def setYBoundsHigh(self, yBoundsHigh: int):
        raise NotImplementedError

    def getYStepSize(self) -> int:
        raise NotImplementedError

    def setYStepSize(self, yStepSize: int):
        raise NotImplementedError

    def getYDelay_ms(self) -> int:
        raise NotImplementedError

    def setYDelay_ms(self, yDelay_ms: int):
        raise NotImplementedError
    
    def setValuesFromConfig(self, scanConfig: ScanAreaConfig):
        self.setXBoundsLow(scanConfig.XBoundsLow)
        self.setXBoundsHigh(scanConfig.XBoundsHigh)
        self.setXStepSize(scanConfig.XStepSize)
        self.setXDelay_ms(scanConfig.XStepDelay_ms)

        self.setYBoundsLow(scanConfig.YBoundsLow)
        self.setYBoundsHigh(scanConfig.YBoundsHigh)
        self.setYStepSize(scanConfig.YStepSize)
        self.setYDelay_ms(scanConfig.YStepDelay_ms)

    def createAreaScanConfig(self) -> ScanAreaConfig:
        return ScanAreaConfig((self.getXBoundsLow(), self.getXBoundsHigh()), (self.getYBoundsLow(), self.getYBoundsHigh()), 
            (self.getXStepSize(), self.getYStepSize()), (self.getXDelay_ms(), self.getYDelay_ms()))

class VariabledScanAreaConfigurationPanel(ScanAreaConfiguarationPanel):
    """ Panel interface, variable based `ScanAreaConfiguarationPanel`. All configurable values are stored in tkinter variables. """

    _DEFAULT_X_MIN = 1500
    _DEFAULT_X_MAX = 2500
    _DEFAULT_X_STEPSIZE = 5
    _DEFAULT_X_DELAY = 20

    _DEFAULT_Y_MIN = 1500
    _DEFAULT_Y_MAX = 2500
    _DEFAULT_Y_STEPSIZE = 5
    _DEFAULT_Y_DELAY = 100

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._xBoundsLowVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_X_MIN)
        self._xBoundsHighVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_X_MAX)
        self._xStepSizeVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_X_STEPSIZE)
        self._xDelayVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_X_DELAY)

        self._yBoundsLowVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_Y_MIN)
        self._yBoundsHighVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_Y_MAX)
        self._yStepSizeVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_Y_STEPSIZE)
        self._yDelayVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_Y_DELAY)

    @property
    def XBoundsLowVariable(self) -> tkext.IntNoneVar:
        return self._xBoundsLowVariable

    @property
    def XBoundsHighVariable(self) -> tkext.IntNoneVar:
        return self._xBoundsHighVariable

    @property
    def XStepSizeVariable(self) -> tkext.IntNoneVar:
        return self._xStepSizeVariable

    @property
    def XDelayMillisecondsVariable(self) -> tkext.IntNoneVar:
        return self._xDelayVariable

    @property
    def YBoundsLowVariable(self) -> tkext.IntNoneVar:
        return self._yBoundsLowVariable

    @property
    def YBoundsHighVariable(self) -> tkext.IntNoneVar:
        return self._yBoundsHighVariable

    @property
    def YStepSizeVariable(self) -> tkext.IntNoneVar:
        return self._yStepSizeVariable

    @property
    def YDelayMillisecondsVariable(self) -> tkext.IntNoneVar:
        return self._yDelayVariable

    def getXBoundsLow(self) -> int:
        return self._xBoundsLowVariable.get()

    def setXBoundsLow(self, xBoundsLow: int):
        self._xBoundsLowVariable.set(xBoundsLow)

    def getXBoundsHigh(self) -> int:
        return self._xBoundsHighVariable.get()

    def setXBoundsHigh(self, xBoundsHigh: int):
        self._xBoundsHighVariable.set(xBoundsHigh)

    def getXStepSize(self) -> int:
        return self._xStepSizeVariable.get()

    def setXStepSize(self, xStepSize: int):
        self._xStepSizeVariable.set(xStepSize)

    def getXDelay_ms(self) -> int:
        return self._xDelayVariable.get()

    def setXDelay_ms(self, xDelay_ms: int):
        self._xDelayVariable.set(xDelay_ms)

    def getYBoundsLow(self) -> int:
        return self._yBoundsLowVariable.get()

    def setYBoundsLow(self, yBoundsLow: int):
        self._yBoundsLowVariable.set(yBoundsLow)

    def getYBoundsHigh(self) -> int:
        return self._yBoundsHighVariable.get()

    def setYBoundsHigh(self, yBoundsHigh: int):
        self._yBoundsHighVariable.set(yBoundsHigh)

    def getYStepSize(self) -> int:
        return self._yStepSizeVariable.get()

    def setYStepSize(self, yStepSize: int):
        self._yStepSizeVariable.set(yStepSize)

    def getYDelay_ms(self) -> int:
        return self._yDelayVariable.get()

    def setYDelay_ms(self, yDelay_ms: int):
        self._yDelayVariable.set(yDelay_ms)
            
class StandardScanAreaConfiguarationPanel(VariabledScanAreaConfigurationPanel):
    """ Panel which allows to create and configure a `ScanAreaConfig`. """

    _ENTRY_WIDTH = 6
    _ENTRY_PADX = 1

    _TOP_FRAME_PADX = 4
    _TOP_FRAME_PADY = 4

    _ELEMENT_PADX = 4

    _STEPSIZE_MIN_VALUE = 1

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        xFrame = ttk.Frame(self.getTk())
        
        xBoundsFrame = ttk.Frame(xFrame)
        xBoundsLabel = ttk.Label(xBoundsFrame, text = "X - Bounds (Min - Max)")
        xBoundsLowEntry = tkext.IntEntry(xBoundsFrame, width = self._ENTRY_WIDTH, textvariable = self.XBoundsLowVariable)
        xBoundsHighEntry = tkext.IntEntry(xBoundsFrame, width = self._ENTRY_WIDTH, textvariable = self.XBoundsHighVariable)

        xStepSizeFrame = ttk.Frame(xFrame)
        xStepSizeLabel = ttk.Label(xStepSizeFrame, text = "X - Step Size")
        xStepSizeEntry = tkext.IntEntry(xStepSizeFrame, minValue = self._STEPSIZE_MIN_VALUE, width = self._ENTRY_WIDTH, textvariable = self.XStepSizeVariable)

        xDelayFrame = ttk.Frame(xFrame)
        xDelayLabel = ttk.Label(xDelayFrame, text = "X - Delay [ms]")
        xDelayEntry = tkext.IntEntry(xDelayFrame, width = self._ENTRY_WIDTH, textvariable = self.XDelayMillisecondsVariable)

        yFrame = ttk.Frame(self.getTk())
        
        yBoundsFrame = ttk.Frame(yFrame)
        yBoundsLabel = ttk.Label(yBoundsFrame, text = "Y - Bounds (Min - Max)")
        yBoundsLowEntry = tkext.IntEntry(yBoundsFrame, width = self._ENTRY_WIDTH, textvariable = self.YBoundsLowVariable)
        yBoundsHighEntry = tkext.IntEntry(yBoundsFrame, width = self._ENTRY_WIDTH, textvariable = self.YBoundsHighVariable)

        yStepSizeFrame = ttk.Frame(yFrame)
        yStepSizeLabel = ttk.Label(yStepSizeFrame, text = "Y - Step Size")
        yStepSizeEntry = tkext.IntEntry(yStepSizeFrame, minValue = self._STEPSIZE_MIN_VALUE, width = self._ENTRY_WIDTH, textvariable = self.YStepSizeVariable)

        yDelayFrame = ttk.Frame(yFrame)
        yDelayLabel = ttk.Label(yDelayFrame, text = "Y - Delay [ms]")
        yDelayEntry = tkext.IntEntry(yDelayFrame, width = self._ENTRY_WIDTH, textvariable = self.YDelayMillisecondsVariable)

        xBoundsLabel.pack(side = tk.LEFT)
        xBoundsLowEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)
        xBoundsHighEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        xBoundsFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        xStepSizeLabel.pack(side = tk.LEFT)
        xStepSizeEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        xStepSizeFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        xDelayLabel.pack(side = tk.LEFT)
        xDelayEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        xDelayFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        yBoundsLabel.pack(side = tk.LEFT)
        yBoundsLowEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)
        yBoundsHighEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        yBoundsFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        yStepSizeLabel.pack(side = tk.LEFT)
        yStepSizeEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        yStepSizeFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        yDelayLabel.pack(side = tk.LEFT)
        yDelayEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)

        yDelayFrame.pack(side = tk.LEFT, padx = self._ELEMENT_PADX)

        xFrame.pack(side = tk.TOP, padx = self._TOP_FRAME_PADX, pady = self._TOP_FRAME_PADY)
        yFrame.pack(side = tk.TOP, padx = self._TOP_FRAME_PADX, pady = self._TOP_FRAME_PADY)
            
class ScanCreationPanel(Panel):
    """ Panel interface to create a `IScan`. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def createScan(self) -> IScan:
        raise NotImplementedError

class StandardScanCreationPanel(ScanCreationPanel):
    """ Panel interface to create a `Scan` which uses a `ScanAreaConfiguarationPanel`. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def getScanAreaConfigurationPanel(self) -> ScanAreaConfiguarationPanel:
        """ Returns the scan area configuration panel of the panel. """
        raise NotImplementedError

    def getPositioningTime_ms(self) -> int:
        raise NotImplementedError
    
    def setPositioningTime_ms(self, positioningTime_ms: int):
        raise NotImplementedError

    def getXTilt(self) -> int:
        raise NotImplementedError

    def setXTilt(self, xTilt: int):
        raise NotImplementedError

    def getZPosition(self) -> int:
        raise NotImplementedError

    def setZPosition(self, zPosition: int):
        raise NotImplementedError

    def getLaserIntensity(self) -> int:
        raise NotImplementedError

    def setLasetIntensity(self, intensity: int):
        raise NotImplementedError

    def createScan(self) -> Scan:
        raise NotImplementedError

class VariabledStandardScanCreationPanel(StandardScanCreationPanel):
    """ Panel interface, variable based `StandardScanCreationPanel`. All configurable values are stored in tkinter variables. """

    _DEFAULT_POSITIONING_TIME_MS = 5000
    _DEFAULT_ADDITIONAL_SCAN_VALUES = ""

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._positioningTime_msVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_POSITIONING_TIME_MS)
        self._xTiltVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_ADDITIONAL_SCAN_VALUES)
        self._zPositionVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_ADDITIONAL_SCAN_VALUES)
        self._laserIntensityVariable = tkext.IntNoneVar(self.getTk(), self._DEFAULT_ADDITIONAL_SCAN_VALUES)

    @property
    def PositionTime_msVariable(self) -> tkext.IntNoneVar:
        return self._positioningTime_msVariable

    @property
    def XTiltVariable(self) -> tkext.IntNoneVar:
        return self._xTiltVariable

    @property
    def ZPositionVariable(self) -> tkext.IntNoneVar:
        return self._zPositionVariable

    @property
    def LaserIntensityVariable(self) -> tkext.IntNoneVar:
        return self._laserIntensityVariable

    def getPositioningTime_ms(self) -> int:
        return self._positioningTime_msVariable.get()
    
    def setPositioningTime_ms(self, positioningTime_ms: int):
        self._positioningTime_msVariable.set(positioningTime_ms)

    def getXTilt(self) -> int:
        return self._xTiltVariable.get()

    def setXTilt(self, xTilt: int):
        self._xTiltVariable.set(xTilt)

    def getZPosition(self) -> int:
        return self._zPositionVariable.get()

    def setZPosition(self, zPosition: int):
        self._zPositionVariable.set(zPosition)

    def getLaserIntensity(self) -> int:
        return self._laserIntensityVariable.get()

    def setLasetIntensity(self, intensity: int):
        self._laserIntensityVariable.set(intensity)

class StandardStandardScanCreationPanel(VariabledStandardScanCreationPanel):
    """ Panel which allows to create and configure a `Scan`. """

    _ENTRY_WIDTH = 6
    _ENTRY_PADX = 1

    _VARIABLE_PADX = 8
    _VARIABLE_PADY = 4

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._scanAreaConfigurationPanel = self.createPanel(ScanAreaConfiguarationPanel, self.getTk())

        variablesFrame = ttk.Frame(self.getTk())
        gridFrame = ttk.Frame(variablesFrame)

        positioningTimeFrame = ttk.Frame(gridFrame)
        positioningTimeLabel = ttk.Label(positioningTimeFrame, text = "Positioning Time [ms]")
        positioningTimeEntry = tkext.IntEntry(positioningTimeFrame, width = self._ENTRY_WIDTH, textvariable = self.PositionTime_msVariable)
            
        laserIntensityFrame = ttk.Frame(gridFrame)
        laserIntensityLabel = ttk.Label(laserIntensityFrame, text = "Laser Intensity")
        #laserIntensityLabel = ttk.Label(laserIntensityFrame, text = "Laser Intensity (Optional)")
        laserIntensityEntry = tkext.IntEntry(laserIntensityFrame, width = self._ENTRY_WIDTH, textvariable = self.LaserIntensityVariable)
        laserIntensityEntry.bind('<1>', self.setLasetIntensity(self.LaserIntensityVariable))
        laserIntensityEntry.bind('<2>', self.setLasetIntensity(self.LaserIntensityVariable))

        xTiltFrame = ttk.Frame(gridFrame)
        xTiltLabel = ttk.Label(xTiltFrame, text = "X - Tilt (Optional)")
        xTiltEntry = tkext.IntEntry(xTiltFrame, width = self._ENTRY_WIDTH, textvariable = self.XTiltVariable)

        zPositionFrame = ttk.Frame(gridFrame)
        zPositionLabel = ttk.Label(zPositionFrame, text = "Z - Position (Optional)")
        zPositionEntry = tkext.IntEntry(zPositionFrame, width = self._ENTRY_WIDTH, textvariable = self.ZPositionVariable)

        positioningTimeLabel.pack(side = tk.LEFT)
        positioningTimeEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)

        xTiltLabel.pack(side = tk.LEFT)
        xTiltEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)

        zPositionLabel.pack(side = tk.LEFT)
        zPositionEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)

        laserIntensityLabel.pack(side = tk.LEFT)
        laserIntensityEntry.pack(side = tk.RIGHT, padx = self._ENTRY_PADX)

        positioningTimeFrame.grid(row = 0, column = 0, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY, sticky = tk.E)
        xTiltFrame.grid(row = 1, column = 0, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY, sticky = tk.E)
        laserIntensityFrame.grid(row = 0, column = 1, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY, sticky = tk.E)
        zPositionFrame.grid(row = 1, column = 1, padx = self._VARIABLE_PADX, pady = self._VARIABLE_PADY, sticky = tk.E)
        
        gridFrame.pack(side = tk.RIGHT)

        self._scanAreaConfigurationPanel.getTk().pack(side = tk.TOP, fill = tk.X)
        variablesFrame.pack(side = tk.TOP, fill = tk.X)

    def getScanAreaConfigurationPanel(self) -> ScanAreaConfiguarationPanel:
        return self._scanAreaConfigurationPanel

class ScanProgressPanel(Panel):
    """ Panel interface which shows the progress status of an `IScan` and needs to be refreshed manually. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._scan: IScan = None

    @property
    def Scan(self) -> IScan:
        """ The current scan whose progress is shown. """
        return self._scan

    @Scan.setter
    def Scan(self, scan: IScan):
        self._scan = scan
        self.refresh()

    def refresh(self):
        """ Refreshes the shown information about the current scan progress. """
        raise NotImplementedError

class StandardScanProgressPanel(ScanProgressPanel):
    """ Default `ScanProgressPanel` implementation. """

    _SCAN_INFO_NO_SCAN = "No Scan"
    _SCAN_INFO_TEMPLATE = "{0} - {1} - {2:.1%}"
    _SCAN_STATUS_READY = "Ready"
    _SCAN_STATUS_RUNNING = "Running"
    _SCAN_STATUS_COMPLETED = "Completed"
    _SCAN_STATUS_ABORTED = "Aborted"
    _SCAN_STATUS_FAILED = "Failed"

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._scanInfoVariable = tk.StringVar(self.MainFrame, self._SCAN_INFO_NO_SCAN)
        self._scanPercentageVariable = tk.DoubleVar(self.MainFrame, 0.)

        textFrame = ttk.Frame(self.MainFrame)
        infoLabel = ttk.Label(textFrame, textvariable = self._scanInfoVariable)
        
        progressFrame = ttk.Frame(self.MainFrame)
        progressBar = ttk.Progressbar(progressFrame, orient = tk.HORIZONTAL, variable = self._scanPercentageVariable, maximum = 1.)

        infoLabel.pack(side = tk.TOP)
        textFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

        progressBar.pack(side = tk.TOP, fill = tk.X, expand = True)
        progressFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

    def refresh(self):
        scanInfo = self._SCAN_INFO_NO_SCAN
        scanPercentage = 0.0

        if self.Scan is not None:
            scanName = self.Scan.getName()
            
            if self.Scan.isRunning():
                scanStatus = self._SCAN_STATUS_RUNNING
            elif self.Scan.isCompleted():
                scanStatus = self._SCAN_STATUS_COMPLETED
            elif self.Scan.isAborted():
                scanStatus = self._SCAN_STATUS_ABORTED
            elif self.Scan.isFinished():
                scanStatus = self._SCAN_STATUS_FAILED
            else:
                scanStatus = self._SCAN_STATUS_READY

            scanPercentage = self.Scan.getProgressPercentage()
            scanInfo = self._SCAN_INFO_TEMPLATE.format(scanName, scanStatus, scanPercentage)
            
        self._scanInfoVariable.set(scanInfo)
        self._scanPercentageVariable.set(scanPercentage)

class ScanCreationDialog(OkAbortDialog):
    """ Dialog interface which creates a `IScan` based on a `ScanCreationPanel`. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._scanPanel: ScanCreationPanel = self._createScanCreationPanel()

    @property
    def ScanCreationPanel(self) -> ScanCreationPanel:
        return self._scanPanel
    
    @showerror
    def _onOk(self):
        self.Result = self._scanPanel.createScan()
        self.close()

    @showerror
    def _onAbort(self):
        self.close()

    def _createScanCreationPanel(self) -> ScanCreationPanel:
        raise NotImplementedError

class StandardScanCreationDialog(ScanCreationDialog):
    """ Dialog interface which creates a `IScan` based on a `StandardScanCreationPanel`. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> StandardScanCreationPanel:
        raise NotImplementedError

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardScanAreaConfiguarationPanel)
manifest.insert(StandardScanProgressPanel)