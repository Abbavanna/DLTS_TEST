"""
Extension which adds a binary save and load service for `IScanImage`s.

Implementations
---------------
Services: `BinaryScanImageDataService`.
"""
from typing import Sequence, Dict, Union, Collection
from pathlib import Path

from dltscontrol.dlts import IScanImage

import gzip
import pickle
import jsonpickle

# extension dependencies
from dltscontrol.app.objectsaving import SaveService, LoadService

class BinaryScanImageSaveError(Exception):
    """ Scan image couldn't be serialized or saved. """
    pass

class BinaryScanImageLoadError(Exception):
    """ Scan image couldn't be deserialized or loaded. """
    pass

class BinaryScanImageDataService(SaveService[IScanImage], LoadService[IScanImage]):
    """ Save and load service which serializes and deserializes `IScanImage`s to and from binary files. 
    
    Supports serialization and deserialization with python's default `pickle` or with `jsonpickle` whose serialized objects can be edited with a text editor.
    Additionally supports compression of serialized objects using `gzip`. 
    """
    _JSON_FILE_ENCODING = "utf-8"

    _TO_FILE = "Binary"
    _FROM_FILE = _TO_FILE

    _LEGACY_BINARY_COMPRESSED_SUFFIX = ".bsc"
    _LEGACY_JSON_BINARY_COMPRESSED_SUFFIX = ".jsc"

    _LEGACY_COMPRESSED_SUFFIXES = (_LEGACY_BINARY_COMPRESSED_SUFFIX, _LEGACY_JSON_BINARY_COMPRESSED_SUFFIX)
    
    _BINARY_SUFFIX = ".bsi"
    _JSON_BINARY_SUFFIX = ".jsi"
    _GZIP_SUFFIX = ".gz"

    _BINARY_COMPRESSED_SUFFIX = _BINARY_SUFFIX + _GZIP_SUFFIX
    _JSON_BINARY_COMPRESSED_SUFFIX = _JSON_BINARY_SUFFIX + _GZIP_SUFFIX

    _BINARY_SUFFIXES = (_BINARY_SUFFIX, _BINARY_COMPRESSED_SUFFIX, _LEGACY_BINARY_COMPRESSED_SUFFIX)
    _JSON_BINARY_SUFFIXES = (_JSON_BINARY_SUFFIX, _JSON_BINARY_COMPRESSED_SUFFIX, _LEGACY_JSON_BINARY_COMPRESSED_SUFFIX)
    _COMPRESSED_SUFFIXES = (_BINARY_COMPRESSED_SUFFIX, _JSON_BINARY_COMPRESSED_SUFFIX) + _LEGACY_COMPRESSED_SUFFIXES

    _SAVE_SUFFIXES = (_BINARY_SUFFIX, _BINARY_COMPRESSED_SUFFIX, _JSON_BINARY_SUFFIX, _JSON_BINARY_COMPRESSED_SUFFIX)
    _LOAD_SUFFIXES = _SAVE_SUFFIXES + _LEGACY_COMPRESSED_SUFFIXES

    _SAVE_FORMAT_DESCRIPTIONS = {_BINARY_SUFFIX: "Binary Scan Image", 
                                _BINARY_COMPRESSED_SUFFIX: "Binary Scan Image Compressed",
                                _JSON_BINARY_SUFFIX: "Binary Json Scan Image",
                                _JSON_BINARY_COMPRESSED_SUFFIX: "Binary Json Scan Image Compressed (Recommended)"}
    
    _LOAD_FORMAT_DESCRIPTIONS = dict(_SAVE_FORMAT_DESCRIPTIONS)
    _LOAD_FORMAT_DESCRIPTIONS.update(
                                {_LEGACY_BINARY_COMPRESSED_SUFFIX: "Legacy Binary Scan Image Compressed", 
                                _LEGACY_JSON_BINARY_COMPRESSED_SUFFIX: "Legacy Binary Json Scan Image Compressed"})

    def getSaveFormats(self) -> Sequence[str]:
        return self._SAVE_SUFFIXES

    def getLoadFormats(self) -> Sequence[str]:
        return self._LOAD_SUFFIXES

    # def getDefaultSaveFormat(self) -> str:
    #     return self._JSON_BINARY_COMPRESSED_SUFFIX

    def getSaveFormatDescriptions(self) -> Dict[str, str]:
        return self._SAVE_FORMAT_DESCRIPTIONS

    def getLoadFormatDescriptions(self) -> Dict[str, str]:
        return self._LOAD_FORMAT_DESCRIPTIONS

    def getToFileName(self) -> str:
        return self._TO_FILE

    def getFromFileName(self) -> str:
        return self._FROM_FILE

    def _saveTo(self, objectToSave: Union[IScanImage, Collection[IScanImage]], location: Path):
        suffix = "".join(location.suffixes)

        if suffix in self._BINARY_SUFFIXES:
            binary = pickle.dumps(objectToSave)
        elif suffix in self._JSON_BINARY_SUFFIXES:
            binary = jsonpickle.dumps(objectToSave).encode(self._JSON_FILE_ENCODING)
        else:
            raise BinaryScanImageSaveError("Can't determine serialization algorithm from suffix: {}. Supported Suffixes: {}.".format(suffix, self._SAVE_SUFFIXES))
        
        if suffix in self._COMPRESSED_SUFFIXES:
            binary = gzip.compress(binary)
        
        location.write_bytes(binary)

    def _loadFrom(self, location: Path) -> Union[IScanImage, Collection[IScanImage]]:
        suffix = "".join(location.suffixes)

        binary = location.read_bytes()

        if suffix in self._COMPRESSED_SUFFIXES:
            binary = gzip.decompress(binary)

        if suffix in self._BINARY_SUFFIXES:
            scanImage = pickle.loads(binary)
        elif suffix in self._JSON_BINARY_SUFFIXES:
            scanImage = jsonpickle.loads(binary.decode(self._JSON_FILE_ENCODING))
        else:
            raise BinaryScanImageLoadError("Can't determine deserialization algorithm from suffix: {}. Supported Suffixes: {}.".format(suffix, self._LOAD_SUFFIXES))
        
        return scanImage

# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(BinaryScanImageDataService, savetype = IScanImage, tofile = BinaryScanImageDataService._TO_FILE, savecollection = True, 
    loadtype = IScanImage, fromfile = BinaryScanImageDataService._FROM_FILE, loadcollection = True)