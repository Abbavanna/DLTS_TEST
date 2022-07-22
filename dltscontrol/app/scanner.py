""" 
Extension which adds the scanner applet to allow the user to create, start and control scans. 

Implementations
---------------
Applets: `Scanner`
"""
from typing import Sequence, Dict, List
from pathlib import Path

from dltscontrol.apptk import Component, Service, Applet, Panel, Context, showerror
from dltscontrol.dlts import IScan, ScanAreaConfig

import re

import numpy as np

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import rootLogger, IDltsComponent, IUserConfigComponent
from dltscontrol.app.scanning import IScanCreationComponent, ScanProgressPanel
from dltscontrol.app.objectsaving import ISaveServiceComponent

logger = rootLogger.getChild(__name__)

class Scanner(Applet, IDltsComponent, IScanCreationComponent, ISaveServiceComponent, IUserConfigComponent):
    """ An applet to create, start and stop user parameterized scans based on scan creation services. 
    
    The scanner allows to create and start scans which are provided by scan creation services. The scanner keeps track of the 
    scan progress and provides the means to control the started scan. Additionally it comes with an automatic and user-configuarable
    scan raw data logger.

    Used Panels
    -----------
    `ScanProgressPanel`
    """
    _REFRESH_PERIOD_MS = 1000
    _RAW_DATA_LOG_PERIOD_MS = 3000

    _BUTTON_WIDTH = 10

    _FRAME_PADX = 2
    _FRAME_PADY = 2

    _DEFAULT_SCAN_NAME = "None"

    _RAW_DATA_LOG_SECTION = "Scanner Raw Data Log Defaults"

    _RAW_DATA_LOG_ENABLED_KEY = "enabled"
    _RAW_DATA_LOG_ENABLED_DEFAULT = "True"

    _RAW_DATA_LOG_FORMAT_KEY = "format"
    _RAW_DATA_LOG_FORMAT_DEFAULT = "None"

    _RAW_DATA_LOG_DIRECTOY_KEY = "directory-name"
    _RAW_DATA_LOG_DIRECTOY_DEFAULT = "ScanRawDataLog"

    _RAW_DATA_LOG_DATE_FORMAT_KEY = "date-format"
    _RAW_DATA_LOG_DATE_FORMAT_DEFAULT = "%Y%m%d-%H%M%S"

    _RAW_DATA_LOG_FILE_NAME_FORMAT_KEY = "name-format"
    _RAW_DATA_LOG_FILE_NAME_FORMAT_DEFAULT = "{date}_{name}_x{xmin}-{xmax}_y{ymin}-{ymax}_z{z}_xt{xtilt}_i{intensity}_{index}"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Scanner")

        self.Window.geometry("600x80")
        self.Window.resizable(True, True)

        self._scan: IScan = None
        self._periodicRefreshCaller = tkext.PeriodicCaller(self.getTk(), self._REFRESH_PERIOD_MS, self.refresh)
        self._selectedScanNameVariable = tk.StringVar(self.getTk(), self._DEFAULT_SCAN_NAME)

        self._rawDataLogCaller = tkext.PeriodicCaller(self.getTk(), self._RAW_DATA_LOG_PERIOD_MS, self._logScanRawData)
        self._scanImagesLoggedStateList: List[bool] = list()

        self._rawLogTimeFormat = self._RAW_DATA_LOG_DATE_FORMAT_DEFAULT
        self._rawLogFileNameFormat = self._RAW_DATA_LOG_FILE_NAME_FORMAT_DEFAULT
        self._rawLogRelativeDirectory = Path(self._RAW_DATA_LOG_DIRECTOY_DEFAULT)

        self._rawLogEnabledVariable = tk.BooleanVar(self.getTk(), self._RAW_DATA_LOG_ENABLED_DEFAULT)
        self._rawLogFormatVariable = tk.StringVar(self.getTk(), self._RAW_DATA_LOG_FORMAT_DEFAULT)
        
        creationFrame = ttk.Frame(self.getTk())

        rawDataCheckButton = ttk.Checkbutton(creationFrame, text = "Raw Data Log:", variable = self._rawLogEnabledVariable, command = self._updateRawDataLogCaller)
        self._rawDataFormatOptionMenu = tkext.OptionMenu(creationFrame, self._rawLogFormatVariable, self._RAW_DATA_LOG_FORMAT_DEFAULT)

        self._creationOptionMenu = tkext.OptionMenu(creationFrame, self._selectedScanNameVariable, self._DEFAULT_SCAN_NAME)
        self._selectedScanNameVariable.set('Multi Intensity Scan')  # TODO: DEBUG.. Remove me later

        startButton = ttk.Button(creationFrame, text = "Start", width = self._BUTTON_WIDTH, command = self._onScanStartClick)
        abortButton = ttk.Button(creationFrame, text = "Abort", width = self._BUTTON_WIDTH, command = self._onScanAbortClick)

        self._scanProgressPanel = self.createPanel(ScanProgressPanel, self.getTk())

        rawDataCheckButton.pack(side = tk.LEFT)
        self._rawDataFormatOptionMenu.pack(side = tk.LEFT, padx = self._FRAME_PADX, pady = self._FRAME_PADY)
        abortButton.pack(side = tk.RIGHT)
        startButton.pack(side = tk.RIGHT, padx = self._FRAME_PADX, pady = self._FRAME_PADY)

        self._creationOptionMenu.pack(side = tk.RIGHT)

        creationFrame.pack(side = tk.TOP, fill = tk.X, padx = self._FRAME_PADX, pady = self._FRAME_PADY)
        self._scanProgressPanel.MainFrame.pack(side = tk.BOTTOM, fill = tk.X, padx = self._FRAME_PADX, pady = self._FRAME_PADY)

    @property
    def Scan(self) -> IScan:
        """ The current scan. """
        return self._scan

    @Scan.setter
    def Scan(self, scan: IScan):
        if self._scan is not scan:
            self._scan = scan
            self._scanProgressPanel.Scan = scan
            self._scanImagesLoggedStateList.clear()

    @property
    def RawDataLogEnabled(self) -> bool:
        return self._rawLogEnabledVariable.get() and self.SelectedRawLogFormat != self._RAW_DATA_LOG_FORMAT_DEFAULT

    @property
    def SelectedRawLogFormat(self) -> str:
        return self._rawLogFormatVariable.get()

    def onCreate(self):
        super().onCreate()

        self._rawDataFormatOptionMenu.Options = self.getToFileNamesForType(np.ndarray)
        self._creationOptionMenu.Options = self.getScanNames()

        userConfig = self.getUserConfig()

        if userConfig is not None:
            self._rawLogEnabledVariable.set(userConfig.getSet(self._RAW_DATA_LOG_SECTION, self._RAW_DATA_LOG_ENABLED_KEY, self._RAW_DATA_LOG_ENABLED_DEFAULT))
            self._rawLogFormatVariable.set(userConfig.getSet(self._RAW_DATA_LOG_SECTION, self._RAW_DATA_LOG_FORMAT_KEY, 
                next(iter(self._rawDataFormatOptionMenu.Options), self._RAW_DATA_LOG_FORMAT_DEFAULT)))

            self._rawLogRelativeDirectory = userConfig.getSet(self._RAW_DATA_LOG_SECTION, self._RAW_DATA_LOG_DIRECTOY_KEY, self._RAW_DATA_LOG_DIRECTOY_DEFAULT)
            self._rawLogTimeFormat = userConfig.getSet(self._RAW_DATA_LOG_SECTION, self._RAW_DATA_LOG_DATE_FORMAT_KEY, self._RAW_DATA_LOG_DATE_FORMAT_DEFAULT)
            self._rawLogFileNameFormat = userConfig.getSet(self._RAW_DATA_LOG_SECTION, self._RAW_DATA_LOG_FILE_NAME_FORMAT_KEY, self._RAW_DATA_LOG_FILE_NAME_FORMAT_DEFAULT)

        self._rawLogDirectory = self.getContext().Application.WorkingDirectory / self._rawLogRelativeDirectory

        if not self._rawLogDirectory.exists():
            self._rawLogDirectory.mkdir()

        self._updateRawDataLogCaller()

    def onFocusIn(self, event):
        if not self._periodicRefreshCaller.IsRunning:
            self._periodicRefreshCaller.start()
    
    def onFocusOut(self, event):
        if self._periodicRefreshCaller.IsRunning:
            self._periodicRefreshCaller.cancel()

    @showerror
    def _onScanStartClick(self):
        """ Called when the user clicks on the scan start button. Creates the selected scan using a scan factory service and start it afterwards. """
        scan = self.requestScanCreationService(self._selectedScanNameVariable.get()).createScan()
        
        if scan is not None:
            dlts = self.getDlts()

            if dlts is not None:
                dlts.startScan(scan)
                self.Scan = scan
    
    @showerror
    def _onScanAbortClick(self):
        """ Called when the user clicks the scan abort button. Trys to abort the current scan. """
        if self.Scan is not None and self.Scan.isRunning():
            self.Scan.abort()

    def _updateRawDataLogCaller(self):
        if self.RawDataLogEnabled:
            if not self._rawDataLogCaller.IsRunning:
                self._rawDataLogCaller.start()
        else:
            if self._rawDataLogCaller.IsRunning:
                self._rawDataLogCaller.cancel()

    def _logScanRawData(self):
        """ Called periodically if raw data log is enabled. Saves the array raw data contained by the current scan's scan images in a user-configurable format using save services. """
        try:    
            if self.Scan is not None:
                for scanImageIndex, scanImage in enumerate(self.Scan.getScanImages()):
                    if len(self._scanImagesLoggedStateList) <= scanImageIndex:
                        self._scanImagesLoggedStateList.append(False)
                    
                    if not self._scanImagesLoggedStateList[scanImageIndex] and (scanImage.isCompleted() or self.Scan.isFinished()):
                        self._scanImagesLoggedStateList[scanImageIndex] = True
                        
                        saveService = self.requestSaveService(np.ndarray, self.SelectedRawLogFormat)

                        position = scanImage.getPosition()
                        size = scanImage.getSize()

                        name = "".join(map(lambda match: match[-1], re.findall("(^|\s)([A-Z])", scanImage.getName())))
                        if not name:
                            name = scanImage.getName()

                        date = scanImage.getScanDate()
                        dateString = date.strftime(self._rawLogTimeFormat) if date is not None else "#NA"

                        xmin = position[0]
                        xmax = xmin + size[0]
                        ymin = position[1]
                        ymax = ymin + size[1]

                        fileName = self._rawLogFileNameFormat.format(date = dateString, name = name, xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax,
                            z = scanImage.getZPosition(), xtilt = scanImage.getXTilt(), intensity = scanImage.getLaserIntensity(), index = scanImageIndex)

                        saveService.save(scanImage.getImageArray(), self._rawLogDirectory / fileName)
        except Exception as ex:
            logger.exception("Raw data logging has failed. Reason: %s", ex)

    def refresh(self):
        """ Called periodically. Checks the service-provided DLTS for any scans and refreshs the scan progress panel. """
        if self.Scan is None and self.IsDltsPresent:
            dlts = self.getDlts()

            if dlts is not None and dlts.Scan is not None:
                self.Scan = dlts.Scan

        self._scanProgressPanel.refresh()

# extension area

from dltscontrol.app.manifest import manifest

# applets
manifest.insert(Scanner, entry = "Scanner", root = True)