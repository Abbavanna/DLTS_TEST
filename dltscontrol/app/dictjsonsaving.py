"""
Extension which adds a save and load service to save and load jsonable dictionaries to and from json.

Implementations
---------------
Services: `DictionaryJsonDataService`.
"""
from typing import Dict
from pathlib import Path

from dltscontrol.app.objectsaving import SaveService, LoadService

import json

class DictionaryJsonDataService(SaveService[Dict], LoadService[Dict]):
    """ Service to load and save dictionaries from and to Json. """

    _FILE_FORMATS = (".jsn", ".json")
    _FILE_NAME = "Json"

    _JSON_FILE_ENCODING = "utf-8"
    _JSON_INDENT_LEVEL = 4

    def isSaveable(self, objectToSave: Dict):
        saveable = isinstance(objectToSave, Dict)

        if saveable:
            try:
                json.dumps(objectToSave)
            except:
                saveable = False

        return saveable

    def getSaveFormats(self):
        return self._FILE_FORMATS

    def getLoadFormats(self):
        return self._FILE_FORMATS

    def getToFileName(self):
        return self._FILE_NAME

    def getFromFileName(self):
        return self._FILE_NAME

    def _saveTo(self, objectToSave: Dict, location: Path):
        location.write_text(json.dumps(objectToSave, indent = self._JSON_INDENT_LEVEL), self._JSON_FILE_ENCODING)

    def _loadFrom(self, location: Path) -> Dict:
        return json.loads(location.read_text(self._JSON_FILE_ENCODING))

# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(DictionaryJsonDataService, savetype = dict, tofile = DictionaryJsonDataService._FILE_NAME, 
    loadtype = dict, fromfile = DictionaryJsonDataService._FILE_NAME)