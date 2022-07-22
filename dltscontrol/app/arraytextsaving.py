"""
Extension which adds a save service to save the data of one or two dimensional `numpy.ndarray`s to text.

Implementations
---------------
Services: `ArrayTextSaveService`.
"""
from typing import Sequence
from pathlib import Path

import numpy as np

# extension dependencies
from dltscontrol.app.core import IUserConfigComponent
from dltscontrol.app.objectsaving import SaveService

class ArrayNotSaveableAsTextError(Exception):
    """ The `numpy.ndarray` is not saveable as text since it's not supported for any reason. """
    pass

class ArrayTextSaveService(SaveService[np.ndarray], IUserConfigComponent):
    """ Saves and serializes 1D or 2D `numpy.ndarray`s to csv and optionally compressed text files. Delimiter and value format are user-configureable. """

    _SAVE_FORMATS = (".csv", ".csv.gz")

    _TO_FILE = "Text"

    _USER_CONFIG_SECTION = "Array Data Text Saving"

    _CSV_DELIMITER_KEY = "delimiter"
    _CSV_DELIMITER_DEFAULT = ";"

    _CSV_VALUE_FORMAT_KEY = "format"
    _CSV_VALUE_FORMAT_DEFAULT = "%.5g"

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._delimiter = self._CSV_DELIMITER_DEFAULT
        self._format = self._CSV_VALUE_FORMAT_DEFAULT
    
    def onRequest(self, **requestProperties):
        userConfig = self.getUserConfig()

        if userConfig is not None:
            self._delimiter = userConfig.getSet(self._USER_CONFIG_SECTION, self._CSV_DELIMITER_KEY, self._CSV_DELIMITER_DEFAULT)
            self._format = userConfig.getSet(self._USER_CONFIG_SECTION, self._CSV_VALUE_FORMAT_KEY, self._CSV_VALUE_FORMAT_DEFAULT)

    def isSaveable(self, objectToSave: np.ndarray) -> bool:
        return isinstance(objectToSave, np.ndarray) and self._isSaveableDataShape(objectToSave) and self._isSaveableDataFormat(objectToSave)

    def _isSaveableDataShape(self, array: np.ndarray) -> bool:
        return len(array.shape) <= 2

    def _isSaveableDataFormat(self, array: np.ndarray) -> bool:
        return np.issubdtype(array.dtype, np.floating) or np.issubdtype(array.dtype, np.integer) or np.issubdtype(array.dtype, np.character)

    def getSaveFormats(self) -> Sequence[str]:
        return self._SAVE_FORMATS

    def getToFileName(self) -> str:
        return self._TO_FILE

    def _saveTo(self, objectToSave: np.ndarray, location: Path):
        if not self._isSaveableDataShape(objectToSave):
            raise ArrayNotSaveableAsTextError("Array to save needs to be in an appropriate shape. Shape '{}' is not supported.".format(objectToSave.shape))
        
        if not self._isSaveableDataFormat(objectToSave):
            raise ArrayNotSaveableAsTextError("Array to save needs to be of an appropriate data type. Data type '{}' is not supported.".format(objectToSave.dtype))

        np.savetxt(location.as_posix(), objectToSave, delimiter = self._delimiter, fmt = self._format)

# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(ArrayTextSaveService, savetype = np.ndarray, tofile = ArrayTextSaveService._TO_FILE)      