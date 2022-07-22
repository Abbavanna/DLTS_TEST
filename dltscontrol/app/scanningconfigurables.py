"""
Configurable components for scanning purposes.

Derivables
----------
Dialogs: `ConfigurableStandardScanCreationDialog`
"""

from typing import Dict

import tkinter as tk

# extension dependencies
from dltscontrol.app.core import rootLogger, IUserConfigComponent, IUserConfig
from dltscontrol.app.scanning import StandardScanCreationPanel, StandardScanCreationDialog
from dltscontrol.app.dictconfigurables import MenuedServicedDictConfigurableWindow

logger = rootLogger.getChild(__name__)

class ConfigurableStandardScanCreationDialog(StandardScanCreationDialog, MenuedServicedDictConfigurableWindow, IUserConfigComponent):
    """ `ScanCreationDialog` which uses a `IUserConfig` to load its panel default values and allows saving and loading those values to and from files. """

    _LOAD_FROM_LAST_TIME = "load-from-last-time"

    _X_MIN = "x-min"
    _X_MAX = "x-max"
    _X_STEPSIZE = "x-step"
    _X_DELAY = "x-delay"

    _Y_MIN = "y-min"
    _Y_MAX = "y-max"
    _Y_STEPSIZE = "y-step"
    _Y_DELAY = "y-delay"

    _POSITIONING_TIME = "positioning-time"

    _X_TILT = "x-tilt"
    _Z_POSITION = "z-position"
    _LASER_INTENSITY = "laser-intensity"

    _LOAD_FROM_LAST_TIME_DEFAULT = 1

    _X_MIN_DEFAULT = 1500
    _X_MAX_DEFAULT = 2500
    _X_STEPSIZE_DEFAULT = 5
    _X_DELAY_DEFAULT = 20

    _Y_MIN_DEFAULT = 1500
    _Y_MAX_DEFAULT = 2500
    _Y_STEPSIZE_DEFAULT = 5
    _Y_DELAY_DEFAULT = 100

    _POSITIONING_TIME_DEFAULT = 5000

    _X_TILT_DEFAULT = ""
    _Z_POSITION_DEFAULT = ""
    _LASER_INTENSITY_DEFAULT = ""

    """ This field marks the section of the user config and may be overridden by subclasses to use a different default value set. """
    _DEFAULT_USER_CONFIG_SECTION = "Scan Dialog"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._setAsNewDefaultsVariable = tk.BooleanVar(self.getTk(), self._LOAD_FROM_LAST_TIME_DEFAULT)

        self.getConfigurationMenu().add_separator()
        self.getConfigurationMenu().add_checkbutton(label = "As new defaults", variable = self._setAsNewDefaultsVariable)

    def onCreate(self):
        super().onCreate()

        userConfig = self.getUserConfig()

        if userConfig is not None:
            try:
                self._loadConfigValues(userConfig)
            except Exception as ex:
                logger.exception(ex)
    
    def onResultSet(self, result):
        super().onResultSet(result)

        if self._setAsNewDefaultsVariable.get() and result is not None:
            userConfig = self.getUserConfig()

            if userConfig is not None:
                try:
                    self._saveConfigValues(userConfig)
                except Exception as ex:
                    logger.exception(ex)

    def getConfigurationMenuLabel(self):
        return "Parameters"

    def saveConfigToDict(self, values: Dict):
        scanCreationPanel: StandardScanCreationPanel = self.ScanCreationPanel
        areaConfigurationPanel = scanCreationPanel.getScanAreaConfigurationPanel()

        values[self._X_MIN] = areaConfigurationPanel.getXBoundsLow()
        values[self._X_MAX] = areaConfigurationPanel.getXBoundsHigh()
        values[self._X_STEPSIZE] = areaConfigurationPanel.getXStepSize()
        values[self._X_DELAY] = areaConfigurationPanel.getXDelay_ms()

        values[self._Y_MIN] = areaConfigurationPanel.getYBoundsLow()
        values[self._Y_MAX] = areaConfigurationPanel.getYBoundsHigh()
        values[self._Y_STEPSIZE] = areaConfigurationPanel.getYStepSize()
        values[self._Y_DELAY] = areaConfigurationPanel.getYDelay_ms()

        values[self._POSITIONING_TIME] = scanCreationPanel.getPositioningTime_ms()

        xTilt = scanCreationPanel.getXTilt() 
        zPosition = scanCreationPanel.getZPosition()
        laserIntensity = scanCreationPanel.getLaserIntensity()

        values[self._X_TILT] = xTilt if xTilt is not None else ""
        values[self._Z_POSITION] = zPosition if zPosition is not None else ""
        values[self._LASER_INTENSITY] = laserIntensity if laserIntensity is not None else ""
        print("values is :", values)

    def loadConfigFromDict(self, values: Dict):
        scanCreationPanel: StandardScanCreationPanel = self.ScanCreationPanel
        areaConfigurationPanel = scanCreationPanel.getScanAreaConfigurationPanel()

        areaConfigurationPanel.setXBoundsLow(values.get(self._X_MIN, areaConfigurationPanel.getXBoundsLow()))
        areaConfigurationPanel.setXBoundsHigh(values.get(self._X_MAX, areaConfigurationPanel.getXBoundsHigh()))
        areaConfigurationPanel.setXStepSize(values.get(self._X_STEPSIZE, areaConfigurationPanel.getXStepSize()))
        areaConfigurationPanel.setXDelay_ms(values.get(self._X_DELAY, areaConfigurationPanel.getXDelay_ms()))
    
        areaConfigurationPanel.setYBoundsLow(values.get(self._Y_MIN, areaConfigurationPanel.getYBoundsLow()))
        areaConfigurationPanel.setYBoundsHigh(values.get(self._Y_MAX, areaConfigurationPanel.getYBoundsHigh()))
        areaConfigurationPanel.setYStepSize(values.get(self._Y_STEPSIZE, areaConfigurationPanel.getYStepSize()))
        areaConfigurationPanel.setYDelay_ms(values.get(self._Y_DELAY, areaConfigurationPanel.getYDelay_ms()))

        scanCreationPanel.setPositioningTime_ms(values.get(self._POSITIONING_TIME, scanCreationPanel.getPositioningTime_ms()))
        
        scanCreationPanel.setXTilt(values.get(self._X_TILT, scanCreationPanel.getXTilt()))
        scanCreationPanel.setZPosition(values.get(self._Z_POSITION, scanCreationPanel.getZPosition()))
        scanCreationPanel.setLasetIntensity(values.get(self._LASER_INTENSITY, scanCreationPanel.getLaserIntensity()))
        

    def _loadConfigValues(self, userConfig: IUserConfig):
        """ Loads the values of the user config into the entry fields when the dialog opens. """
        scanCreationPanel: StandardScanCreationPanel = self.ScanCreationPanel
        areaConfigurationPanel = scanCreationPanel.getScanAreaConfigurationPanel()

        self._setAsNewDefaultsVariable.set(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._LOAD_FROM_LAST_TIME, self._LOAD_FROM_LAST_TIME_DEFAULT))

        areaConfigurationPanel.setXBoundsLow(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._X_MIN, self._X_MIN_DEFAULT)))
        areaConfigurationPanel.setXBoundsHigh(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._X_MAX, self._X_MAX_DEFAULT)))
        areaConfigurationPanel.setXStepSize(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._X_STEPSIZE, self._X_STEPSIZE_DEFAULT)))
        areaConfigurationPanel.setXDelay_ms(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._X_DELAY, self._X_DELAY_DEFAULT)))
    
        areaConfigurationPanel.setYBoundsLow(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._Y_MIN, self._Y_MIN_DEFAULT)))
        areaConfigurationPanel.setYBoundsHigh(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._Y_MAX, self._Y_MAX_DEFAULT)))
        areaConfigurationPanel.setYStepSize(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._Y_STEPSIZE, self._Y_STEPSIZE_DEFAULT)))
        areaConfigurationPanel.setYDelay_ms(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._Y_DELAY, self._Y_DELAY_DEFAULT)))

        scanCreationPanel.setPositioningTime_ms(int(userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._POSITIONING_TIME, self._POSITIONING_TIME_DEFAULT)))

        xTilt = userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._X_TILT, self._X_TILT_DEFAULT)
        zPosition = userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._Z_POSITION, self._Z_POSITION_DEFAULT)
        laserIntensity = userConfig.getSet(self._DEFAULT_USER_CONFIG_SECTION, self._LASER_INTENSITY, self._LASER_INTENSITY_DEFAULT)

        if xTilt:
            scanCreationPanel.setXTilt(int(xTilt))
        
        if zPosition:
            scanCreationPanel.setZPosition(int(zPosition))

        if laserIntensity:
            scanCreationPanel.setLasetIntensity(int(laserIntensity))
            

    def _saveConfigValues(self, userConfig: IUserConfig):
        """ Saves the entry values back to the user config when the dialog is about to get closed to be used as next default values. """
        scanCreationPanel: StandardScanCreationPanel = self.ScanCreationPanel
        areaConfigurationPanel = scanCreationPanel.getScanAreaConfigurationPanel()

        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._X_MIN, areaConfigurationPanel.getXBoundsLow())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._X_MAX, areaConfigurationPanel.getXBoundsHigh())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._X_STEPSIZE, areaConfigurationPanel.getXStepSize())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._X_DELAY, areaConfigurationPanel.getXDelay_ms())

        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._Y_MIN, areaConfigurationPanel.getYBoundsLow())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._Y_MAX, areaConfigurationPanel.getYBoundsHigh())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._Y_STEPSIZE, areaConfigurationPanel.getYStepSize())
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._Y_DELAY, areaConfigurationPanel.getYDelay_ms())

        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._POSITIONING_TIME, scanCreationPanel.getPositioningTime_ms())

        xTilt = scanCreationPanel.getXTilt() 
        zPosition = scanCreationPanel.getZPosition()
        laserIntensity = scanCreationPanel.getLaserIntensity()

        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._X_TILT, xTilt if xTilt is not None else "")
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._Z_POSITION, zPosition if zPosition is not None else "")
        userConfig.set(self._DEFAULT_USER_CONFIG_SECTION, self._LASER_INTENSITY, laserIntensity if laserIntensity is not None else "")