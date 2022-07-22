"""
Extension for basic DLTS command and control.

Applets
-------
`MainController`. See: `apptk.getContext().startApplet`.
"""
from typing import Dict

from dltscontrol.apptk import Applet, showerror

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as tkm
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import rootLogger, IDltsComponent, IUserConfigComponent, DltsService

logger = rootLogger.getChild(__name__)

class MainController(Applet, IDltsComponent, IUserConfigComponent):
    """ Applet for common control tasks of the DLTS like simple laser positioning. 
    
    The main controller consists of a bunch of value scales/scales to manipulate the position and laser of the DLTS. It allows to fire a user 
    defined laser pulse and monitors laser reflections if desired by the user. Additionally the user can manually connect to and disconnect 
    from the DLTS. The bounds of the value scales a configureable through a user config service.

    Used Panels
    -----------
    None
    """
    _USER_CONFIG_SECTION = "Controller Value Scales"

    _USER_CONFIG_APPLY_KEY = "apply-delay-ms"
    _USER_CONFIG_X_MIN_KEY = "x-min"
    _USER_CONFIG_X_MAX_KEY = "x-max"
    _USER_CONFIG_Y_MIN_KEY = "y-min"
    _USER_CONFIG_Y_MAX_KEY = "y-max"
    _USER_CONFIG_Z_MIN_KEY = "z-min"
    _USER_CONFIG_Z_MAX_KEY = "z-max"
    _USER_CONFIG_X_TILT_MIN_KEY = "x-tilt-min"
    _USER_CONFIG_X_TILT_MAX_KEY = "x-tilt-max"
    _USER_CONFIG_LASER_INTENSITY_MIN_KEY = "laser-intensity-min"
    _USER_CONFIG_LASER_INTENSITY_MAX_KEY = "laser-intensity-max"

    _X_POSITION_NAME = "X Position"
    _Y_POSITION_NAME = "Y Position"
    _Z_POSITION_NAME = "Z Position"
    _X_TILT_NAME = "X Tilt"
    _LASER_INTENSITY_NAME = "Laser Intensity"

    _SCALE_NAMES = [_X_POSITION_NAME, _Y_POSITION_NAME, _Z_POSITION_NAME, _X_TILT_NAME, _LASER_INTENSITY_NAME]
    _SCALE_MIN_MAX_KEYS = {_X_POSITION_NAME: (_USER_CONFIG_X_MIN_KEY, _USER_CONFIG_X_MAX_KEY),
                            _Y_POSITION_NAME: (_USER_CONFIG_Y_MIN_KEY, _USER_CONFIG_Y_MAX_KEY),
                            _Z_POSITION_NAME: (_USER_CONFIG_Z_MIN_KEY, _USER_CONFIG_Z_MAX_KEY),
                            _X_TILT_NAME: (_USER_CONFIG_X_TILT_MIN_KEY, _USER_CONFIG_X_TILT_MAX_KEY),
                            _LASER_INTENSITY_NAME: (_USER_CONFIG_LASER_INTENSITY_MIN_KEY, _USER_CONFIG_LASER_INTENSITY_MAX_KEY),}

    _SCALE_DEFAULT_MIN_VALUE = 0
    _SCALE_DEFAULT_MAX_VALUE = 4096

    _DEFAULT_ENTRY_WIDTH = 8

    _DEFAULT_PADDING = 2

    _REFRESH_PERIOD_MS = 1000
    _REFLECTION_UPDATE_PERIOD_MS = 500

    """ Slider runs infinitely in one direction if another window is opened immediately after the scale value has been changed by leftclicking 
    right or left to the slider. Seems to be some kind of mouse key release event issue which happens completely outside of tkinter event system 
    which can be accessed from python code. The following delay makes sure that all mouse events have been processed before anything else happens. """
    _SCALE_DLTS_SET_DELAY_DEFAULT = 150 # 100ms worked on my pc so 150ms should be sufficient

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)
        
        self.Window.title("Controller")
        self.Window.geometry("450x300")

        self.createMenuBarIfNotExistent()

        dltsMenu = tk.Menu(self.MenuBar, tearoff = False)
        dltsMenu.add_command(label = "Connect", command = self._onConnectToDltsClick)
        dltsMenu.add_command(label = "Disconnect", command = self._onDisconnectFromDlts)

        self.MenuBar.add_cascade(menu = dltsMenu, label = "DLTS")

        self._refreshCaller = tkext.PeriodicCaller(self.Window, self._REFRESH_PERIOD_MS, self._refreshValuesTask)
        self._updateReflectionCaller = tkext.PeriodicCaller(self.Window, self._REFLECTION_UPDATE_PERIOD_MS, self._laserReflectionUpdateTask)

        self._scaleScaleVariables: Dict[str, tk.DoubleVar] = dict()
        self._scaleDltsUpdateTaskIds: Dict[str, int] = dict()
        
        self._laserReflectionVariable = tkext.IntNoneVar(self.getTk(), "")
        self._laserReflectionUpdateVariable = tk.BooleanVar(self.getTk(), False)

        self._laserPulseIntensityVariable = tkext.IntNoneVar(self.getTk(), "")
        self._laserPulseFrequencyVariable = tkext.IntNoneVar(self.getTk(), "")

        self._scaleApplyDelay_ms = self._SCALE_DLTS_SET_DELAY_DEFAULT

        userConfig = self.getUserConfig()

        if userConfig is not None:
            self._scaleApplyDelay_ms = int(userConfig.getSet(self._USER_CONFIG_SECTION, self._USER_CONFIG_APPLY_KEY, self._SCALE_DLTS_SET_DELAY_DEFAULT))

        # build value scales
        scaleFrame = ttk.Frame(self.getTk(), relief = tkext.TK_RELIEF_SUNKEN, padding = 2 * self._DEFAULT_PADDING)
        scaleFrame.grid_columnconfigure(2, weight = 1)

        for scaleIndex, scaleName in enumerate(self._SCALE_NAMES):
            scaleIndex *= 2
            separatorIndex = scaleIndex - 1

            scaleFrame.grid_rowconfigure(scaleIndex, weight = 1)

            if userConfig is not None:
                minKey, maxKey = self._SCALE_MIN_MAX_KEYS[scaleName]
                minValue = int(userConfig.getSet(self._USER_CONFIG_SECTION, minKey, self._SCALE_DEFAULT_MIN_VALUE))
                maxValue = int(userConfig.getSet(self._USER_CONFIG_SECTION, maxKey, self._SCALE_DEFAULT_MAX_VALUE))
            else:
                minValue = self._SCALE_DEFAULT_MIN_VALUE
                maxValue = self._SCALE_DEFAULT_MAX_VALUE
            
            entryVariable = tkext.IntNoneVar(scaleFrame, minValue)
            scaleVariable = tk.DoubleVar(scaleFrame, minValue)

            self._scaleScaleVariables[scaleName] = scaleVariable
            
            label = ttk.Label(scaleFrame, text = scaleName)
            entry = tkext.IntEntry(scaleFrame, minValue = minValue, maxValue = maxValue, textvariable = entryVariable, width = self._DEFAULT_ENTRY_WIDTH)
            entry.bind(tkext.TK_EVENT_RETURN, 
                lambda event, entryVariable = entryVariable, scaleVariable = scaleVariable: 
                    self._onSliderEntryReturn(event, entryVariable, scaleVariable))
            entry.bind(tkext.TK_EVENT_KEYPAD_ENTER, 
                lambda event, entryVariable = entryVariable, scaleVariable = scaleVariable: 
                    self._onSliderEntryReturn(event, entryVariable, scaleVariable))
            scale = ttk.Scale(scaleFrame, from_ = minValue, to = maxValue, variable = scaleVariable)

            # bind mouse wheel
            tkext.bindMouseWheel(scale, 
                lambda event, scaleVariable = scaleVariable, minValue = minValue, maxValue = maxValue: 
                    self._onSliderMouseWheel(event, scaleVariable, minValue, maxValue))
            tkext.bindMouseWheel(entry, 
                lambda event, scaleVariable = scaleVariable, minValue = minValue, maxValue = maxValue: 
                    self._onSliderMouseWheel(event, scaleVariable, minValue, maxValue))
            tkext.bindMouseWheel(label,  
                lambda event, scaleVariable = scaleVariable, minValue = minValue, maxValue = maxValue: 
                    self._onSliderMouseWheel(event, scaleVariable, minValue, maxValue))
            
            # trace scale value to update DLTS
            scaleVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, 
                lambda name, index, mode, scale = scale, scaleName = scaleName: 
                    self._onScaleValueChange(scale, scaleName))
            
            # bind entry to scale value
            scaleVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, 
                lambda name, index, mode, scaleVariable = scaleVariable, entryVariable = entryVariable: 
                    entryVariable.set(scaleVariable.get()))

            if separatorIndex > 0:
                separator = ttk.Separator(scaleFrame)
                separator.grid(row = separatorIndex, column = 0, columnspan = 3, sticky = tk.NSEW, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)

            label.grid(row = scaleIndex, column = 0, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
            entry.grid(row = scaleIndex, column = 1, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
            scale.grid(row = scaleIndex, column = 2, sticky = tk.EW, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
            
        scaleFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True, padx = 2 * self._DEFAULT_PADDING, pady = 2 * self._DEFAULT_PADDING)
            
        # build laser pulse panel     
        laserPulseFrame = ttk.Frame(self.getTk(), relief = tkext.TK_RELIEF_SUNKEN, padding = 2 * self._DEFAULT_PADDING)

        laserPulseHeading = ttk.Label(laserPulseFrame, text = "Laser Pulse", justify = tk.LEFT)
        laserPulseLowerFrame = ttk.Frame(laserPulseFrame)

        laserPulseButton = ttk.Button(laserPulseLowerFrame, text = "Fire", command = self._onLaserPulseClick, width = 10)
        laserPulseIntensityLabel = ttk.Label(laserPulseLowerFrame, text = "Intensity")
        laserPulseIntensityEntry = tkext.IntEntry(laserPulseLowerFrame, textvariable = self._laserPulseIntensityVariable, width = self._DEFAULT_ENTRY_WIDTH)
        laserPulseFrequencyLabel = ttk.Label(laserPulseLowerFrame, text = "Frequency")
        laserPulseFrequencyEntry = tkext.IntEntry(laserPulseLowerFrame, textvariable = self._laserPulseFrequencyVariable, width = self._DEFAULT_ENTRY_WIDTH)

        laserPulseButton.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserPulseFrequencyEntry.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserPulseFrequencyLabel.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserPulseIntensityEntry.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserPulseIntensityLabel.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)

        laserPulseHeading.pack(side = tk.TOP, fill = tk.X, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserPulseLowerFrame.pack(side = tk.TOP, fill = tk.X)

        laserPulseFrame.pack(side = tk.TOP, fill = tk.X, padx = 2 * self._DEFAULT_PADDING, pady = 2 * self._DEFAULT_PADDING)

        # build laser reflection display
        laserReflectionFrame = ttk.Frame(self.getTk(), relief = tkext.TK_RELIEF_SUNKEN, padding = 2 * self._DEFAULT_PADDING)
        valueLabel = ttk.Label(laserReflectionFrame, textvariable = self._laserReflectionVariable, width = self._DEFAULT_ENTRY_WIDTH,
            padding = self._DEFAULT_PADDING, background = "white", relief = tkext.TK_RELIEF_SUNKEN)
        updateCheckButton = ttk.Checkbutton(laserReflectionFrame, text = "Update Laser Reflection", variable = self._laserReflectionUpdateVariable,
            command = self._onUpdateLaserReflectionChange)

        updateCheckButton.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        valueLabel.pack(side = tk.RIGHT, padx = self._DEFAULT_PADDING, pady = self._DEFAULT_PADDING)
        laserReflectionFrame.pack(side = tk.TOP, fill = tk.X, padx = 2 * self._DEFAULT_PADDING, pady = 2 * self._DEFAULT_PADDING)

        self.onFocusIn(None)  # TODO: Keep if you like
        
    def _onSliderEntryReturn(self, event, entryVariable: tkext.IntNoneVar, scaleVariable: tk.DoubleVar):
        """ Called when user hits the return button inside of a scale attached entry. Writes the value of the entry variable into the scale/scale variable. """
        entryValue = entryVariable.get()
        currentValue = int(scaleVariable.get())

        if entryValue is not None and entryValue != currentValue:
            scaleVariable.set(entryValue)
    
    def _onSliderMouseWheel(self, event, scaleVariable: tk.DoubleVar, minValue: int, maxValue: int):
        """ Called when the users moves the mouse wheel and the cursor is right above a value scale. Increments and decrements the scale value. """
        if self.IsFocusIn:
            delta = event.delta
            value = int(scaleVariable.get())

            if delta < 0:
                value -= 1
            elif delta > 0:
                value += 1
            
            if value >= minValue and value <= maxValue:
                scaleVariable.set(value)
            else:
                self.getTk().bell()

    def _onScaleValueChange(self, scale: ttk.Scale, scaleName: str):
        """ Called when one of the scales values has been changed. Sends the new value to the connected DLTS after a short delay to prevent buggy scale slider moving infinitely. """
        
        if scaleName in self._scaleDltsUpdateTaskIds:
            scale.after_cancel(self._scaleDltsUpdateTaskIds.pop(scaleName))

        self._scaleDltsUpdateTaskIds[scaleName] = scale.after(self._scaleApplyDelay_ms, self._setScaleDltsValue, scale, scaleName)
        
    @showerror
    def _setScaleDltsValue(self, scale: ttk.Scale, scaleName: str):
        """ Sends the value of the given scale and name to the connected DLTS. """
        if scaleName in self._scaleDltsUpdateTaskIds:
            self._scaleDltsUpdateTaskIds.pop(scaleName)

        value = int(scale.get())
        dlts = self.getDlts()

        if dlts is not None:
            if scaleName == self._X_POSITION_NAME:
                dlts.setX(value)
            elif scaleName == self._Y_POSITION_NAME:
                dlts.setY(value)
            elif scaleName == self._Z_POSITION_NAME:
                dlts.setZ(value)
            elif scaleName == self._X_TILT_NAME:
                dlts.setXTilt(value)
            elif scaleName == self._LASER_INTENSITY_NAME:
                dlts.setLaserIntensity(value)
            
    @showerror
    def _onLaserPulseClick(self):
        """ Called when the users click on the laser pulse fire button. Issues a laser pulse at the connected DLTS. """
        dlts = self.getDlts()
        if dlts is not None:
            dlts.fireLaserPulse(self._laserPulseIntensityVariable.get(), self._laserPulseFrequencyVariable.get())

    def _checkLaserReflectionUpdateTask(self):
        """ Checks if the displayed laser reflection value shall be updated and starts a periodic calling task if necessary. """
        update = self._laserReflectionUpdateVariable.get() and self.IsFocusIn

        if update:
            if not self._updateReflectionCaller.IsRunning:
                self._updateReflectionCaller.start(False)
        else:
            if self._updateReflectionCaller.IsRunning:
                self._updateReflectionCaller.cancel()
    
    def _onUpdateLaserReflectionChange(self):
        """ Called when the users changes or clicks on the laser reflection checkbutton. """
        self._checkLaserReflectionUpdateTask()
    
    @showerror
    def _onConnectToDltsClick(self):
        """ Called when the user click on 'DLTS->Connect'. Trys to connect to a DLTS by making as dlts service request. """
        if self.IsDltsPresent:

            if tkm.askokcancel("Active DLTS Connection", "An existing DLTS Connection has been detected, close all existing connections?", parent = self.getContext().getTk()):
                self.disconnectDlts()

        self.getDlts()

    @showerror
    def _onDisconnectFromDlts(self):
        """ Called when the users clicks on 'DLTS->Disconnect'. Stops any running dlts service. """
        self.disconnectDlts()

    def _refreshValuesTask(self):
        """ Trys to refresh all shown DLTS values like x position, laser intensity etc.. Called periodically on focus gain until a commandable DLTS is available. """
        stopTask = False

        try:
            if self.IsDltsPresent:
                dlts = self.getDlts()

                if dlts is not None and dlts.IsConnected and not dlts.IsScanRunning:
                    stopTask = True
                    self._scaleScaleVariables[self._X_POSITION_NAME].set(dlts.getX())
                    self._scaleScaleVariables[self._Y_POSITION_NAME].set(dlts.getY())
                    self._scaleScaleVariables[self._Z_POSITION_NAME].set(dlts.getZ())
                    self._scaleScaleVariables[self._X_TILT_NAME].set(dlts.getXTilt()) 
                    self._scaleScaleVariables[self._LASER_INTENSITY_NAME].set(dlts.getLaserIntensity()) 

                    self._laserPulseIntensityVariable.set(dlts.getLaserPulseIntensity()) 
                    self._laserPulseFrequencyVariable.set(dlts.getLaserPulseFrequency())
        except Exception as ex:
            stopTask = True
            logger.exception(ex)

        return stopTask
    
    def _laserReflectionUpdateTask(self):
        """ Trys to fetch the current laser reflection value from the conncted DLTS and writes it to the appropriate variable. 
        Called periodically if activated by the user. 
        """
        stopTask = False

        try:
            dlts = self.getDlts()

            if dlts is not None:
                if dlts.IsConnected and not dlts.IsScanRunning:
                    self._laserReflectionVariable.set(dlts.getLaserReflectionValue())
                else:
                    self._laserReflectionVariable.set(None)
            else:
                stopTask = True
        except Exception as ex:
            stopTask = True
            logger.exception(ex)

        if stopTask:
            self._laserReflectionUpdateVariable.set(False)

        return stopTask

    def onCreate(self):
        super().onCreate()

        self.getDlts()

    def onFocusIn(self, event):
        from dltscontrol.color_print import cprint
        cprint(f'onFocusIn', 'debug_r')

        super().onFocusIn(event)
        # TODO: DEBUG.. Remove all below me later
        if not hasattr(self, 'singlerun'):
            setattr(self, 'singlerun', True)
        if self.singlerun:
            if not self._refreshCaller.IsRunning:
                self._refreshCaller.start()

            self._checkLaserReflectionUpdateTask()
            self.singlerun = False

    def onFocusOut(self, event):
        super().onFocusOut(event)

        if self._refreshCaller.IsRunning:
            self._refreshCaller.cancel()

        self._checkLaserReflectionUpdateTask()

# extension area

from dltscontrol.app.manifest import manifest

# applets
manifest.insert(MainController, entry = "Controller", root = True, start = True)