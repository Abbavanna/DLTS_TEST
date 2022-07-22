""" 
Extenison which provides applets to show, depicture and save scan data. 

Implementations
---------------
Applets: `ScanDataViewer` and `ScanImageInfoViewer`.
"""
from typing import Type, Tuple, Sequence, Union, List

from dltscontrol.apptk import Applet, showerror
from dltscontrol.dlts import IScanImage, IScan

import numpy as np

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import IDltsComponent
from dltscontrol.app.scandataviewing import ScanImageViewerPanel, ScanImageInfoPanel
from dltscontrol.app.objectsaving import ISaveServiceComponent, ILoadServiceComponent, FileNameDialogAbortedError

class ScanImageInfoViewer(Applet):
    """ Applet which shows the information contained in the provided scan images. The scan images have to be passed in a collection on start of the applet.
        
    Note
    ----
    For the scan images start property key see: `ScanImageInfoViewer._SCAN_IMAGES_KEY`
    
    Used Panels
    -----------
    `ScanImageInfoPanel`
    """
    class ScanImageInfoViewingError(Exception):
        """ Error during scan image viewing. """
        pass
    
    _SCAN_IMAGES_KEY = "scanimages"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.resizable(False, False)
        self.Window.title("Scan Image Info")

        self._scanImagesInfoPanel = self.createPanel(ScanImageInfoPanel, self.getTk())

        self._scanImagesInfoPanel.MainFrame.pack(fill = tk.BOTH)

    def onStart(self, **startProperties):
        super().onStart(**startProperties)

        scanImages = startProperties.get(self._SCAN_IMAGES_KEY, None)

        if scanImages is None:
            raise self.ScanImageInfoViewingError("Can't show scan image information without a scan image.")

        self._scanImagesInfoPanel.setScanImages(scanImages)

class ScanDataViewer(Applet, IDltsComponent, ISaveServiceComponent, ILoadServiceComponent):
    """ Applet which is capable of showing all the depictable data in a `IScanImage` of a `IScan`. It may start an
    additional applet, the `ScanImageInfoViewer`, to show furhter information and data of the scan image.
    
    Used Panels
    -----------
    `ScanImageViewerPanel`
    """
    REFRESH_PERIOD_MS = 1000

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._scan: IScan = None
        self._scanImages: Tuple[IScanImage] = None

        self._updateFromScanVariable = tk.BooleanVar(self.Window, True)

        self._periodicRefreshCaller = tkext.PeriodicCaller(self.Window, ScanDataViewer.REFRESH_PERIOD_MS, self.refresh)  

        self.Window.title("Scan Image Data")
        self.Window.geometry("1200x600")
        self.createMenuBarIfNotExistent()

        self._scanImagesPanel = self.createPanel(ScanImageViewerPanel, self.getTk())
        self._scanImagesPanel.MainFrame.pack(fill = tk.BOTH, expand = True)

        self._saveMenu = tk.Menu(self.MenuBar, tearoff = False)
        saveAllMenu = tk.Menu(self._saveMenu, tearoff = False)

        for saveServiceClass in self.getSaveServiceClassesForType(IScanImage):
            if self.isCollectionSavable(saveServiceClass):
                toFile = self.getToFileName(saveServiceClass)

                saveAllMenu.add_command(label = "To {}".format(toFile), 
                    command = lambda saveServiceClass = saveServiceClass: self.onSaveAllToFileClick(saveServiceClass))

        self._saveMenu.add_cascade(label = "All", menu = saveAllMenu)

        self._saveSinglesDataMenu = tk.Menu(self._saveMenu, tearoff = False)
        self._saveSinglesMenus: List[tk.Menu] = list()

        self._saveMenu.add_cascade(label = "Singles", menu = self._saveSinglesDataMenu)

        self.buildSaveSinglesMenu()

        self._loadMenu = tk.Menu(self.MenuBar, tearoff = False)
        
        loadAllMenu = tk.Menu(self._loadMenu, tearoff = False)
        loadAddMenu = tk.Menu(self._loadMenu, tearoff = False)

        for loadServiceClass in self.getLoadServiceClassesForType(IScanImage):
            fromFile = self.getFromFileName(loadServiceClass)
            
            loadAddMenu.add_command(label = "From {}".format(fromFile), 
                    command = lambda loadServiceClass = loadServiceClass: self.onLoadAddFromFileClick(loadServiceClass))

            if self.isCollectionLoadable(loadServiceClass):
                loadAllMenu.add_command(label = "From {}".format(fromFile), 
                    command = lambda loadServiceClass = loadServiceClass: self.onLoadAllFromFileClick(loadServiceClass))               

        self._loadMenu.add_cascade(label = "All", menu = loadAllMenu)
        self._loadMenu.add_cascade(label = "Add", menu = loadAddMenu)
        self._loadMenu.add_separator()
        self._loadMenu.add_checkbutton(label = "Update from Scan", variable = self._updateFromScanVariable, command = self.onUpdateFromScanClick)
        
        self.MenuBar.add_cascade(label = "Save", menu = self._saveMenu)
        self.MenuBar.add_cascade(label = "Load", menu = self._loadMenu)
        self.MenuBar.add_command(label = "Info", command = self.onInfoClick)

        # from dltscontrol.app.reflectionscanning import ReflectionScanDataPoint, ReflectionImage
        # from dltscontrol.app.latchupscanning import LatchupScanDataPoint, LatchupImage

        # import datetime
        # import random

        # res1 = (10, 10)
        # res2 = (15, 30)
        # size1 = (2000, 2000)
        # size2 = (1500, 3000)
        # dataReflection1 = [ReflectionScanDataPoint(random.randint(0, 255).to_bytes(1, "big")) for _ in range(res1[0] * res1[1])]
        # dataReflection2 = [ReflectionScanDataPoint(random.randint(0, 255).to_bytes(1, "big")) for _ in range(res2[0] * res2[1])]
        # dataLatchup1 = [LatchupScanDataPoint(random.randint(0, 65535).to_bytes(2, "big")) for _ in range(res1[0] * res1[1])]
        # dataLatchup2 = [LatchupScanDataPoint(random.randint(0, 65535).to_bytes(2, "big")) for _ in range(res2[0] * res2[1])]

        # customLatchup = LatchupImage([LatchupScanDataPoint(value.to_bytes(2, "big")) for value in (0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0)],
        #     (1000, 1000), (80, 20), (8, 2), 1000, 3000, 2048, datetime.datetime.now(), datetime.timedelta(hours = 0.025))

        # reflectionImage1 = ReflectionImage(dataReflection1, (1000, 1000), size1, res1, 1000, 3000, 2048, datetime.datetime.now(), datetime.timedelta(hours = 1.2312))
        # reflectionImage2 = ReflectionImage(dataReflection2, (1000, 1000), size2, res2, 800, 3000, 2048, datetime.datetime.now(), datetime.timedelta(hours = 3.8312))
        # latchupImage1 = LatchupImage(dataLatchup1, (1000, 1000), size1, res1, 2000, 3000, 2048, datetime.datetime.now(), datetime.timedelta(hours = 33.872))
        # latchupImage2 = LatchupImage(dataLatchup2, (1000, 1000), size2, res2, 4000, 3000, 2048, datetime.datetime.now(), datetime.timedelta(hours = 2.54))

        # self.ScanImages = (reflectionImage1, latchupImage1, reflectionImage2, latchupImage2, customLatchup)
 
    @property
    def ScanImages(self) -> Tuple[IScanImage]:
        """ The current scan image. """
        return self._scanImages

    @ScanImages.setter
    def ScanImages(self, scanImages: Tuple[IScanImage]):
        self._scanImages = scanImages
        self.buildSaveSinglesMenu()
        self._scanImagesPanel.setScanImages(self._scanImages)
        self._scanImagesPanel.draw()

    @property
    def Scan(self) -> IScan:
        """ The Current scan. """
        return self._scan

    @Scan.setter
    def Scan(self, scan: IScan):
        self._scan = scan

        if scan is not None:
            self.ScanImages = scan.getScanImages()

    @property
    def UpdateFromScan(self) -> bool:
        """ If the scan image shall be updated from the current scan running at the DLTS. """
        return self._updateFromScanVariable.get()

    @UpdateFromScan.setter
    def UpdateFromScan(self, updateFromScan: bool):
        self._updateFromScanVariable.set(updateFromScan)

    def refresh(self):
        """ Called periodically. """
        if self.UpdateFromScan:
            if self.Scan is None:
                if self.IsDltsPresent:
                    dlts = self.getDlts()
                    
                    if dlts is not None and dlts.Scan is not None:
                        self.Scan = dlts.Scan
            else:
                if not self.ScanImages or self.Scan.isRunning() or \
                    (self.Scan.isCompleted() and any(map(lambda scanImage: not scanImage.isCompleted(), self.ScanImages))):
                    
                    self.ScanImages = self.Scan.getScanImages()
    
    def buildSaveSinglesMenu(self):
        """ Builds the menu bar menu Save->Single->... to allow saving of ech single scan image and its raw data. """
        self._saveSinglesDataMenu.delete(0, tk.END)

        for menu in self._saveSinglesMenus:
            menu.destroy()

        self._saveSinglesMenus.clear()

        if self._scanImages:
            for scanImage in self._scanImages:
                singleMenu = tk.Menu(self._saveSinglesDataMenu, tearoff = False)

                for saveServiceClass in self.getSaveServiceClassesForType(IScanImage):
                    toFile = self.getToFileName(saveServiceClass)

                    singleMenu.add_command(label = "To {}".format(toFile), 
                        command = lambda saveServiceClass = saveServiceClass, objectToSave = scanImage: 
                            self.onSaveSingleToFileClick(saveServiceClass, objectToSave))
                
                for saveServiceClass in self.getSaveServiceClassesForType(np.ndarray):
                    toFile = self.getToFileName(saveServiceClass)

                    singleMenu.add_command(label = "To {}".format(toFile), 
                        command = lambda saveServiceClass = saveServiceClass, objectToSave = scanImage.getImageArray(): 
                            self.onSaveSingleToFileClick(saveServiceClass, objectToSave))
                
                self._saveSinglesDataMenu.add_cascade(label = scanImage.getName(), menu = singleMenu)
                self._saveSinglesMenus.append(singleMenu)
    
    @showerror
    def onLoadAllFromFileClick(self, loadServiceClass: Type):
        """ Called when the user click on 'Load->All->From <FromFileName>'. Requests the selected load service class to load a serialized scan image. """        
        try:
            loadedImages = self.getComponentContext().requestService(loadServiceClass).load()
            
            if isinstance(loadedImages, IScanImage):
                self.ScanImages = (loadedImages, )
            elif loadedImages:
                self.ScanImages = tuple(loadedImages)

            self.UpdateFromScan = False
        except FileNameDialogAbortedError:
            pass
    
    @showerror
    def onLoadAddFromFileClick(self, loadServiceClass: Type):
        """ Called when the user click on 'Load->Add->From <FromFileName>'. Requests the selected load service class to load adn add a serialized scan image. """        
        try:
            loadedImages = self.getComponentContext().requestService(loadServiceClass).load()
            currentImages = self.ScanImages if self.ScanImages is not None else ()
            
            if isinstance(loadedImages, IScanImage):
                self.ScanImages = currentImages + (loadedImages, )
            elif loadedImages:
                self.ScanImages = currentImages + tuple(loadedImages)

            self.UpdateFromScan = False
        except FileNameDialogAbortedError:
            pass
        
    @showerror
    def onSaveAllToFileClick(self, saveServiceClass: Type):
        """ Called when the user clicks 'Save->All->To <ToFileName>'. Requests the selected save service class to serialize and save the current scan image. """
        if self.ScanImages:
            try:
                self.getComponentContext().requestService(saveServiceClass).save(self.ScanImages)
            except FileNameDialogAbortedError:
                pass
                
    @showerror
    def onSaveSingleToFileClick(self, saveServiceClass: Type, objectToSave: Union[IScanImage, np.ndarray]):
        """ Called when the user clicks 'Save->Singles-><Scan Image Name>->To <ToFileName>'. Requests the selected save service class to serialize and save the current scan image. """
        try:
            self.getComponentContext().requestService(saveServiceClass).save(objectToSave)
        except FileNameDialogAbortedError:
            pass

    @showerror
    def onUpdateFromScanClick(self):
        """ Called when the user clicks on the checkbutton 'Load->Update from Scan'. """
        if not self.UpdateFromScan:
            self.Scan = None

        self.refresh()

    @showerror
    def onInfoClick(self):
        """ Called when the users click on 'Info'. Starts the scan image info viewer applet. """
        self.getComponentContext().startApplet(ScanImageInfoViewer, scanimages = self.ScanImages)

    def onFocusIn(self, event):
        if not self._periodicRefreshCaller.IsRunning:
            self._periodicRefreshCaller.start(True)

    def onFocusOut(self, event):
        if self._periodicRefreshCaller.IsRunning:
            self._periodicRefreshCaller.cancel()

# extension area

from dltscontrol.app.manifest import manifest

# applets
manifest.insert(ScanImageInfoViewer, menu = False, appmenu = False)
manifest.insert(ScanDataViewer, entry = "Scan Data", root = True, multiple = True)