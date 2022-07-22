"""
Extension which adds a file based `UserConfigService`.

Implementations
---------------
`ConfigParserUserConfigService`
"""
from typing import Dict, Union
from configparser import ConfigParser
from pathlib import Path

from dltscontrol.apptk import Component, Service

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import IUserConfig, UserConfigService

class ConfigParserUserConfig(IUserConfig):
    """ User config implementation based on a `ConfigParser`. """

    def __init__(self, configParser):
        self._configParser = configParser
    
    @property
    def ConfigParser(self) -> ConfigParser:
        return self._configParser

    def isValueKey(self, section: str, key: str) -> bool:
        return self._configParser.has_option(section, key)

    def isSection(self, section: str) -> bool:
        return self._configParser.has_section(section)

    def get(self, section: str, key: str, defaultValue: str = None) -> str:
        return self._configParser[section][key] if self._configParser.has_option(section, key) else defaultValue

    def getSection(self, section: str) -> Dict:
        return self._configParser[section] if self._configParser.has_section(section) else None

    def set(self, section: str, key: str, value: str):
        if not self._configParser.has_section(section):
            self._configParser.add_section(section)

        if value is not None:
            if not isinstance(value, str):
                value = str(value)

            # percentage signs need to be escaped in file
            value = value.replace("%", "%%")

            self._configParser.set(section, key, value) 
        else: 
            self._configParser.remove_option(section, key)

        if not self._configParser[section]:
            self._configParser.remove_section(section)

    def deleteSection(self, section: str):
        self._configParser.remove_section(section)
    
class ConfigParserUserConfigService(UserConfigService):
    """ User config service which provides access to a file based user configuration. """

    _FILE_NAME = "config.ini"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._configFilePath: Path = self.getContext().Application.WorkingDirectory / self._FILE_NAME
        
        self._userConfig: ConfigParserUserConfig = None

    def onRequest(self, **requestProperties):
        if self._userConfig is None:
            configParser = ConfigParser()

            if self._configFilePath.exists():
                configParser.read(self._configFilePath)

            self._userConfig = ConfigParserUserConfig(configParser)

    def onDestroy(self, event):
        if self._userConfig is not None:
            self._userConfig.ConfigParser.write(open(self._configFilePath, "w+"))

    def getUserConfig(self) -> IUserConfig:
        return self._userConfig

# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(ConfigParserUserConfigService, _global = True)