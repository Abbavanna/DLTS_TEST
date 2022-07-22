"""
Extension which adds a new `IScan`, the `ComboScan`, to the application and provides panels, dialogs and services to create such a scan.

Interfaces
----------
Panels: `ComboScanCreationPanel`.
Dialogs: `ComboScanCreationDialog`. 

Implemetations
--------------
Panels: `StandardComboScanCreationPanel`.
Dialogs: `StandardComboScanCreationDialog`.
Services: `ComboScanCreationService`.
"""
from typing import Sequence, Dict, Tuple

from dltscontrol.apptk import showerror
from dltscontrol.dlts import DltsConnection, IScan, IScanDataPoint, IScanImage

import threading
import datetime
import time

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import rootLogger, OkAbortPanel, PaneledOkAbortDialog
from dltscontrol.app.scanning import ScanCreationPanel, ScanCreationDialog, IScanCreationComponent, ScanCreationService

logger = rootLogger.getChild(__name__)

class ComboScan(IScan):
    """ A scan which combines multiple single scan into one single scan.
    
    The combo scan consists of several single scans whose resulting data images are combined into a even bigger bunch of `IScanImage`s. 
    On start the combo scan starts one scan after another until it gets aborted, fails or all scans have finished. A combo scan can be treated
    as a single usual scan since it implemements the same interface and implements its methods in a reasonable way.

    Known Problem
    -------------

    The combo scan doesn't acquire the dlts connection it is started with. Each single scan of the combo scan acquires it on its own which
    means that there is a small time gap between each scan-finish and next-scan-start in which the dlts connection has not been acquired.
    This is very minor problem, though it can't be fixed at the moment.
    """
    _UPDATE_INTERVAL_S = 1.

    def __init__(self, *scans: Sequence[IScan]):
        self._scans = tuple(scans)
        self._dltsConnection = None

        self._abortRequested = False
        self._thread = threading.Thread(target = self._run)

    @property
    def Scans(self) -> Tuple[IScan]:
        """ All scans of the combo scan. """
        return self._scans

    def getName(self):
        return " + ".join(map(lambda scan: scan.getName(), self.Scans))

    def isRunning(self) -> bool:
        return self._thread.isAlive()

    def isAborted(self) -> bool:
        return any(map(lambda scan: scan.isAborted(), self.Scans)) and not self.isRunning()

    def isFinished(self):
        return all(map(lambda scan: scan.isFinished(), self.Scans)) and not self.isRunning()

    def getStartTime(self) -> datetime.datetime:
        return self.Scans[0].getStartTime()

    def getDuration(self) -> datetime.timedelta:
        return sum(map(lambda scan: scan.getDuration(), self.Scans), datetime.timedelta())

    def getDataPoints(self) -> Tuple[IScanDataPoint]:
        return sum(map(lambda scan: scan.getDataPoints(), self.Scans), ())

    def getScanImages(self) -> Tuple[IScanImage]:
        return sum(map(lambda scan: scan.getScanImages(), self.Scans), ())

    def getScannedPointsCount(self) -> int:
        return len(self.getDataPoints())

    def getScanPointsCount(self) -> int:
        return sum(map(lambda scan: scan.getScanPointsCount(), self.Scans), 0)

    def start(self, dltsConnection: DltsConnection):
        running = self.isRunning()
        finished = self.isFinished()

        if not running and not finished:
            self._dltsConnection = dltsConnection
            self._thread.start()

    def abort(self):
        if self.isRunning() and not self._abortRequested:
            self._abortRequested = True

    def _run(self):
        """ thread function, runs each single scan. """
        try:
            for scan in self.Scans:
            
                if not self.isAborted():
                    
                    scan.start(self._dltsConnection)

                    while not scan.isFinished():

                        if self._abortRequested:
                            scan.abort()
                        
                        time.sleep(self._UPDATE_INTERVAL_S)
        except Exception as ex:
            logger.exception("Combo scan run has failed. Reason: %s", ex)

class ComboScanCreationService(ScanCreationService[ComboScan]):
    """ Scan creation service to create a `ComboScan`. """

    def createScan(self) -> ComboScan:
        return self.getContext().openDialog(ComboScanCreationDialog).waitForResult()

class ComboScanCreationPanel(ScanCreationPanel):
    """ Panel interface to create a `ComboScan`. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def getCombinedScans(self) -> Sequence[IScan]:
        raise NotImplementedError

    def createScan(self) -> ComboScan:
        return ComboScan(*self.getCombinedScans())

class StandardComboScanCreationPanel(ComboScanCreationPanel, IScanCreationComponent):
    """ Default `ComboScanCreationPanel` implementation which uses `ScanCreationService`s to create the individual scans. """

    _DEFAULT_SCAN_OPTION = "None"

    _BUTTON_WIDTH = 10
    _LISTBOX_WIDTH = 50

    _PADY = 2
    _PADX = 2

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        creatorNames = self.getScanNames()

        if not creatorNames:
            creatorNames = (self._DEFAULT_SCAN_OPTION, )

        self._scans: Dict[str, IScan] = dict()

        self._scanCreatorNameVariable = tk.StringVar(self.getTk(), self._DEFAULT_SCAN_OPTION)

        buttonFrameContainer = ttk.Frame(self.getTk())
        buttonFrame = ttk.Frame(buttonFrameContainer)

        optionMenu = tkext.OptionMenu(buttonFrame, self._scanCreatorNameVariable, creatorNames[0], *creatorNames)
        buttonAdd = ttk.Button(buttonFrame, text = "Add", width = self._BUTTON_WIDTH, command = self._onButtonAddClick)
        buttonRemove = ttk.Button(buttonFrame, text = "Remove", width = self._BUTTON_WIDTH, command = self._onButtonRemoveClick)

        listBoxFrame = ttk.Frame(self.getTk())
        
        xScrollbar = ttk.Scrollbar(listBoxFrame, orient = tkext.TK_ORIENT_HORIZONTAL)
        yScrollbar = ttk.Scrollbar(listBoxFrame, orient = tkext.TK_ORIENT_VERTICAL)
        yScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
        xScrollbar.pack(side = tk.BOTTOM, fill = tk.X)

        self._scanListBox = tkext.DragDropListbox(listBoxFrame, width = self._LISTBOX_WIDTH, selectmode = tk.EXTENDED)

        self._scanListBox.config(xscrollcommand = xScrollbar.set, yscrollcommand = yScrollbar.set)
        xScrollbar.config(command = self._scanListBox.xview)
        yScrollbar.config(command = self._scanListBox.yview)

        self._scanListBox.pack(fill = tk.BOTH, expand = True)
    
        optionMenu.grid(row = 0, column = 0, sticky = tk.N, padx = self._PADX, pady = self._PADY)
        buttonAdd.grid(row = 0, column = 1, sticky = tk.N, padx = self._PADX, pady = self._PADY)
        buttonRemove.grid(row = 1, column = 1, sticky = tk.N, padx = self._PADX, pady = self._PADY)

        buttonFrame.pack(side = tk.TOP)

        buttonFrameContainer.pack(side = tk.LEFT, fill = tk.Y)
        listBoxFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

    def getCombinedScans(self):
        scans = list()
        for scanName in self._scanListBox.get(0, tk.END):
            scans.append(self._scans[scanName])
        return scans

    @showerror
    def _onButtonAddClick(self):
        scan = self.requestScanCreationService(self._scanCreatorNameVariable.get()).createScan()

        if scan is not None:
            scanName = "{} - ID: {}".format(scan.getName(), id(scan))
            
            self._scans[scanName] = scan
            self._scanListBox.insert(tk.END, scanName)

            try:
                self.createScan()
            except Exception as ex:
                self._scans.pop(scanName)
                self._scanListBox.delete(tk.END)
                logger.exception(ex)
                raise ex
                
    @showerror
    def _onButtonRemoveClick(self):
        while True:
            selectionIndices= self._scanListBox.curselection()

            if selectionIndices:
                index = selectionIndices[0]
                scanName = self._scanListBox.get(index)
                
                self._scans.pop(scanName)
                self._scanListBox.delete(index)
            else:
                break

class ComboScanCreationDialog(ScanCreationDialog):
    """ Dialog interface which creates a `ComboScan` based on a `ComboScanCreationPanel`. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def _createScanCreationPanel(self) -> ComboScanCreationPanel:
        raise NotImplementedError

class StandardComboScanCreationDialog(ComboScanCreationDialog, PaneledOkAbortDialog):
    """ Default `ComboScanCreationDialog` implementation. """

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure Combo Scan")
        self.Window.resizable(False, False)

        self.ScanCreationPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)
        self.OkAbortPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)

    def _createScanCreationPanel(self):
        return self.createPanel(ComboScanCreationPanel, self.getTk())

    def _createOkAbortPanel(self):
        return self.createPanel(OkAbortPanel, self.getTk())

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardComboScanCreationPanel)

# dialogs
manifest.insert(StandardComboScanCreationDialog)

# services
manifest.insert(ComboScanCreationService, scantype = ComboScan, scanname = "Combo Scan")