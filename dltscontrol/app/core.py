""" 
Extension which provides some basic interface, derivable and helper components. 

Interfaces
----------------
Panels: `OkAbortPanel`
Services: `DltsService` and `UserConfigService`

Derivables
----------
Dialogs: `OkAbortDialog` and `PaneledOkAbortDialog`
Components: `IDltsComponent` and `IUserConfigComponent`. Use those two if you need to interact with a `DltsService` or `UserConfigService` 
since they provide a much more convenient way to interact with them than dealing with the service and context directly.

Implementations
---------------
Panels: `ButtonOkAbortPanel`
"""
from typing import Dict, Union

from dltscontrol.apptk import IComponent, Service, Panel, Dialog, ComponentAvailabilityException
from dltscontrol.dlts import Dlts, DltsConnection
from dltscontrol.event import Event

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

import time

import logging

rootLogger = logging.getLogger("dltscontrol")

logger = rootLogger.getChild(__name__)

class OkAbortPanel(Panel):
    """ Panel interface which provides 'ok' and 'abort' input capabilities. """
    
    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._onOk = Event()
        self._onAbort = Event()

    @property
    def OnOk(self) -> Event:
        """ Event when an 'ok' input has been made. """
        return self._onOk

    @property
    def OnAbort(self) -> Event:
        """ Event when an 'abort' input has been made. """
        return self._onAbort

class ButtonOkAbortPanel(OkAbortPanel):
    """ Button based ok-abort input panel. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        buttonOk = ttk.Button(self.MainFrame, command = self.OnOk, text = "Ok", width = 10)
        buttonAbort = ttk.Button(self.MainFrame, command = self.OnAbort, text = "Abort", width = 10)

        buttonOk.pack(side = tk.LEFT, padx = 2)
        buttonAbort.pack(side = tk.LEFT, padx = 2)

class OkAbortDialog(Dialog):
    """ Dialog which handles and accepts 'ok' and 'abort' from the user. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._addOkAbortKeyEvents()

    def _addOkAbortKeyEvents(self):
        """ Adds key based ok and abort events. Override to manipulate or disable. """
        self.Window.bind(tkext.TK_EVENT_RETURN, lambda event: self._onOk(), tkext.TK_EVENT_BIND_ADD)
        self.Window.bind(tkext.TK_EVENT_KEYPAD_ENTER, lambda event: self._onOk(), tkext.TK_EVENT_BIND_ADD)
        self.Window.bind(tkext.TK_EVENT_ESCAPE, lambda event: self._onAbort(), tkext.TK_EVENT_BIND_ADD)

    def _onOk(self):
        """ Called when the user confirms. """
        raise NotImplementedError

    def _onAbort(self):
        """ Called when the user denys. """
        raise NotImplementedError
        
class PaneledOkAbortDialog(OkAbortDialog):
    """ An ok-abort dialog which additionally uses a `OkAbortPanel` to receive 'ok' and 'abort' input. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._okAbortPanel = self._createOkAbortPanel()
        
        self._okAbortPanel.OnOk.add(self._onOk)
        self._okAbortPanel.OnAbort.add(self._onAbort)

    @property
    def OkAbortPanel(self) -> OkAbortPanel:
        """ The ok-abort panel of the dialog. """
        return self._okAbortPanel

    def _createOkAbortPanel(self) -> OkAbortPanel:
        """ Creates and returns the ok-abort panel of the dialog. """
        raise NotImplementedError

class IUserConfig:
    """ Interface to a configuration in '.ini' format. """

    def isValueKey(self, section: str, key: str) -> bool:
        """ Returns if the section and key combination exists. """
        raise NotImplementedError

    def isSection(self, section: str) -> bool:
        """ Returns if the given section exits. """
        raise NotImplementedError

    def get(self, section: str, key: str, defaultValue: str = None) -> str:
        """ Returns the value for the given section and key combination. If it doesn't exist the default value shall be returned. """
        raise NotImplementedError

    def getSection(self, section: str) -> Dict:
        """ Returns all key value combinations of the given section. 
        Warning
        ------- 
        Depending on the actual implemenation, changes to the returned `Dict` may not be persistent. """
        raise NotImplementedError

    def set(self, section: str, key: str, value: Union[str, int, float, bool, type(None)]):
        """ Creators or updates the value of the given section and key combination. The key shall be deleted if the value is `None`. """
        raise NotImplementedError

    def deleteValue(self, section: str, key: str):
        """ Deletes the value and the given section-key combination. """
        self.set(section, key, None)

    def deleteSection(self, section: str):
        """ Deletes an entire section with all its values and keys. """
        raise NotImplementedError

    def setSection(self, section: str, keyValues: Dict[str, Union[str, int, float, bool, type(None)]], update: bool = True):
        """ Whether updates or sets the given section with the given key-value combinations.
        
        Parameters
        ----------
        update: bool, optional, default = True
            If true all exisitng key-values will be kept and the section will be updated with the given key-values, otherwise the whole section gets deleted beforehand.
        """
        if not update and self.isSection(section):
            self.deleteSection(section)

        if keyValues:
            for key, value in keyValues:
                self.set(section, key, value)

    def getSet(self, section: str, key: str, defaultValue: Union[str, int, float, bool, type(None)]):
        """ Returns the value for the given section and key but creates it beforehand with the given default value if it doesn't exist. """
        if not self.isValueKey(section, key):
            self.set(section, key, defaultValue)
        return self.get(section, key)

class UserConfigService(Service):
    """ Service interface which provides access to a user configuration. Should be always registered as global. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def getUserConfig(self) -> IUserConfig:
        raise NotImplementedError 

class IUserConfigComponent(IComponent):
    """ Provides a more convenient way to interact with a `UserConfigService` than dealing directly with a service. """

    def getUserConfig(self) -> IUserConfig:
        """ Retrieves the user configuration through a `UserConfigService` request. Handles component availability exceptions and returns `None` instead. """
        try:
            userConfigService = self.getContext().requestService(UserConfigService)
        except ComponentAvailabilityException:
            userConfigService = None

        return userConfigService.getUserConfig() if userConfigService is not None else None

    def closeUserConfig(self):
        """ Stops any running `UserConfigService`. """
        self.getContext().stopService(UserConfigService)

    @property
    def IsUserConfigPresent(self) -> bool:
        """ If there is any running `UserConfigService` in the component's context. """
        return self.getContext().isServiceRunning(UserConfigService)

class DltsConnectionError(Exception):
    """ Invalid or inoperational DLTS Connection. """
    pass

class DltsService(Service, IUserConfigComponent):
    """ Service interface which provides access to a DLTS. Should be always registered as global. """

    _RESET_USER_CONFIG_SECTION = "Dlts Disconnect Reset"

    _RESET_ENABLED_KEY = "enabled"
    _SCAN_WAIT_TIMEOUT_KEY = "scan-finish-wait-ms"
    _X_RESET_KEY = "x-position"
    _Y_RESET_KEY = "y-position"
    _Z_RESET_KEY = "z-position"
    _X_TILT_RESET_KEY = "x-tilt"
    _LASER_INTENSITY_RESET_KEY = "laser-intensity"

    _RESET_ENABLED_DEFAULT = 1
    _SCAN_WAIT_TIMEOUT_DEFAULT = 1000
    _X_RESET_DEFAULT = 2048
    _Y_RESET_DEFAULT = 2000
    _Z_RESET_DEFAULT = 2048
    _X_TILT_RESET_DEFAULT = 2048
    _LASER_INTENSITY_RESET_DEFAULT = 0

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._dlts: Dlts = None
        self._dltsConnection: DltsConnection = None

        self._resetEnabled = self._RESET_ENABLED_DEFAULT
        self._xReset = self._X_RESET_DEFAULT
        self._yReset = self._Y_RESET_DEFAULT
        self._zReset = self._Z_RESET_DEFAULT
        self._xTiltReset = self._X_TILT_RESET_DEFAULT
        self._laserIntensityReset = self._LASER_INTENSITY_RESET_DEFAULT
        self._scanFinishWaitTimeout_ms = self._SCAN_WAIT_TIMEOUT_DEFAULT

    def onRequest(self, **requestProperties):
        if self._dltsConnection is None:
            userConfig = self.getUserConfig()

            if userConfig is not None:
                try:
                    self._resetEnabled = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._RESET_ENABLED_KEY, self._RESET_ENABLED_DEFAULT))
                    self._scanFinishWaitTimeout_ms = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._SCAN_WAIT_TIMEOUT_KEY, self._SCAN_WAIT_TIMEOUT_DEFAULT))
                    self._xReset = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._X_RESET_KEY, self._X_RESET_DEFAULT))
                    self._yReset = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._Y_RESET_KEY, self._Y_RESET_DEFAULT))
                    self._zReset = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._Z_RESET_KEY, self._Z_RESET_DEFAULT))
                    self._xTiltReset = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._X_TILT_RESET_KEY, self._X_TILT_RESET_DEFAULT))
                    self._laserIntensityReset = int(userConfig.getSet(self._RESET_USER_CONFIG_SECTION, self._LASER_INTENSITY_RESET_KEY, self._LASER_INTENSITY_RESET_DEFAULT))
                except Exception as ex:
                    logger.exception(ex)

            self._dltsConnection = self._createDltsConnection()
            self._dlts = Dlts(self._dltsConnection)

            # verify connection
            try:
                self._dlts.getX()
            except Exception as ex:
                if self._dltsConnection.IsOpen:
                    self._dltsConnection.close()

                self._dltsConnection = None
                self._dlts = None
                
                raise DltsConnectionError("Dlts connection could not be verified.") from ex

        elif not self._dltsConnection.IsOpen:
            raise DltsConnectionError("Dlts Connection is not longer available or has been closed.")

    def onDestroy(self, event):
        try:
            if self._dlts is not None and self._dlts.IsConnected:
                if self._dlts.IsScanRunning:
                    self._dlts.Scan.abort()

                    waitEndNanos = time.time_ns() + (1000 * self._scanFinishWaitTimeout_ms)
                    
                    # wait until scan has been aborted
                    while self._dlts.Scan.isRunning() and waitEndNanos > time.time_ns():
                        pass

                if self._resetEnabled:
                    self._dlts.setX(self._xReset)
                    self._dlts.setY(self._yReset)
                    self._dlts.setZ(self._zReset)
                    self._dlts.setXTilt(self._xTiltReset)
                    self._dlts.setLaserIntensity(self._laserIntensityReset)
        finally:
            if self._dltsConnection is not None and self._dltsConnection.IsOpen:
                self._dltsConnection.close()
            
    def getDlts(self) -> Dlts:
        """ Returns the DLTS to which a connection has been established. """
        return self._dlts 

    def _createDltsConnection(self) -> DltsConnection:
        """ Creates and returns an new connection to a DLTS. """
        raise NotImplementedError

class IDltsComponent(IComponent):
    """ Provides a more convenient way to interact with a `DltsService` than dealing directly with a service. """

    def getDlts(self) -> Dlts:
        """ Retrieves the DLTS thorugh a `DltsService` request. Handles component availability exceptions and returns `None` instead. """
        try:
            dltsService = self.getContext().requestService(DltsService)
        except ComponentAvailabilityException:
            dltsService = None
        
        return dltsService.getDlts() if dltsService is not None else None

    def disconnectDlts(self):
        """ Stops any present `DltsService` in the component's context. """
        self.getContext().stopService(DltsService)

    @property
    def IsDltsPresent(self):
        """ If there is any `DltsService` already present in the component's context. """
        return self.getContext().isServiceRunning(DltsService)
    
# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(ButtonOkAbortPanel)