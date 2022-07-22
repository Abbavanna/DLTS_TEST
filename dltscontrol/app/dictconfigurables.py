"""
Component templates to implement components configurable through a primitive dictionary.

Note
----
Most likely you want to inherit from: `MenuedServicedDictConfigurableWindow` for user based configurable windows.
"""
from typing import Dict, Union
from pathlib import Path

from dltscontrol.apptk import IComponent, Window, showerror

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import rootLogger
from dltscontrol.app.objectsaving import ISaveServiceComponent, ILoadServiceComponent, FileNameDialogAbortedError

logger = rootLogger.getChild(__name__)

class IDictConfigurableComponent(IComponent):
    """ A component which is configureable through a primitive dictionary. """

    def loadConfigFromDict(self, values: Dict[str, Union[str, int, float, bool]]):
        """ Loads the configurable values from the provided primitive dictionary. To be implemented by sublasses. """
        raise NotImplementedError

    def saveConfigToDict(self, values: Dict[str, Union[str, int, float, bool]]):
        """ Saves the configurable values to the provided primitive dictionary. To be implemented by sublasses."""
        raise NotImplementedError

class IServicedDictConfigurableComponent(IDictConfigurableComponent, ISaveServiceComponent, ILoadServiceComponent):
    """ A configurable component whose configuration can be loaded and saved using load and save services. """
    
    def saveConfigToFile(self, toFileName: str = None, location: Path = None):
        """ Saves the configurable values through a save service. 
        
        Parameters
        ----------
        toFileName: `str` (default: `None`)
            The tofile under which the save service must have been registered. If `None` it is ignored.
        location: `Path` (default: `None`)
            The location to which the configurable values should be saved. If `None` it is ignored.
        """
        try:
            values = dict()
            self.saveConfigToDict(values)
            self.requestSaveService(dict, toFileName).save(values, location)
        except FileNameDialogAbortedError:
            pass
    
    def loadConfigFromFile(self, fromFileName: str = None, location: Path = None):
        """ Loads the configurable values through a load service. 
        
        Parameters
        ----------
        fromFileName: `str` (default: `None`)
            The fromfile under which the load service must have been registered. If `None` it is ignored.
        location: `Path` (default: `None`)
            The location from which the configurable values should be loaded. If `None` it is ignored.
        """
        try:
            self.loadConfigFromDict(self.requestLoadService(dict, fromFileName).load(location))
        except FileNameDialogAbortedError:
            pass

class MenuedDictConfigurableWindow(Window, IDictConfigurableComponent):
    """ A configurable window which comes with a 'save to' and 'load from' menu integrated into the window's menu bar. Menu entries must be filled by subclasses. """

    _CONFIGURATION_CASCADE_MENU_LABEL_DEFAULT = "Configuration"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.createMenuBarIfNotExistent()
        
        self._configurationMenu = tk.Menu(self.MenuBar, tearoff = False)
        self.MenuBar.add_cascade(label = self.getConfigurationMenuLabel(), menu = self._configurationMenu)

        self._saveMenu = tk.Menu(self._configurationMenu, tearoff = False)
        self._loadMenu = tk.Menu(self._configurationMenu, tearoff = False)

        self._configurationMenu.add_cascade(label = "Save to", menu = self._saveMenu)
        self._configurationMenu.add_cascade(label = "Load from", menu = self._loadMenu)

    def getConfigurationMenuLabel(self) -> str:
        """ Returns the name of the menu bar item. """
        return self._CONFIGURATION_CASCADE_MENU_LABEL_DEFAULT

    def getConfigurationMenu(self) -> tk.Menu:
        """ Returns the menu of the menu bar. """
        return self._configurationMenu 

    def getSaveToMenu(self) -> tk.Menu:
        """ Returns the 'save to' menu of the configuration menu. """
        return self._saveMenu

    def getLoadFromMenu(self) -> tk.Menu:
        """ Returns the 'load from' menu of the configuration menu. """
        return self._loadMenu

class MenuedServicedDictConfigurableWindow(MenuedDictConfigurableWindow, IServicedDictConfigurableComponent):
    """ A configurable window whose configuration can be loaded and saved from the menu bar by the user through load and save services. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        saveToMenu = self.getSaveToMenu()
        loadFromMenu = self.getLoadFromMenu()

        toFileNames = self.getToFileNamesForType(dict)
        fromFileNames = self.getFromFileNamesForType(dict)

        if toFileNames:
            if saveToMenu.index(tk.END):
                saveToMenu.add_separator()

            for toFileName in toFileNames:
                saveToMenu.add_command(label = toFileName, command = lambda toFileName = toFileName: self._onSaveToClick(toFileName))
        
        if fromFileNames:
            if loadFromMenu.index(tk.END):
                loadFromMenu.add_separator()

            for fromFileName in fromFileNames:
                loadFromMenu.add_command(label = fromFileName, command = lambda fromFileName = fromFileName: self._onLoadFromClick(fromFileName))

    @showerror
    def _onSaveToClick(self, toFileName: str):
        try:
            self.saveConfigToFile(toFileName)
        except Exception as ex:
            logger.exception(ex)
            raise ex
    
    @showerror
    def _onLoadFromClick(self, fromFileName: str):
        try:
            self.loadConfigFromFile(fromFileName)
        except Exception as ex:
            logger.exception(ex)
            raise ex 