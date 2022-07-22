"""
Extension which adds a save service to save the data of two or three dimensional `numpy.ndarray`s to images.

Implementations
---------------
Services: `ArrayTextSaveService`.
"""
from typing import Sequence
from pathlib import Path

from skimage.io import imsave
from skimage.util import img_as_ubyte
from matplotlib.colors import Normalize

import numpy as np

# extension dependencies
from dltscontrol.app.objectsaving import SaveService

class ArrayNotSaveableAsImageError(Exception):
    """ The `numpy.ndarray` is not saveable as image since it's not supported for any reason. """
    pass

class ArrayImageSaveService(SaveService[np.ndarray]):
    """ Saves and serializes 2D or 3D `numpy.ndarray`s to image files. """

    _SAVE_FORMATS = (".png", ".jpg")

    _TO_FILE = "Image"

    def isSaveable(self, objectToSave: np.ndarray) -> bool:
        return isinstance(objectToSave, np.ndarray) and self._isSaveableDataShape(objectToSave) and self._isSaveableDataFormat(objectToSave)

    def _isSaveableDataShape(self, array: np.ndarray) -> bool:
        return len(array.shape) == 2 or (len(array.shape) == 3 and (array.shape[-1] == 3 or array.shape[-1] == 4))

    def _isSaveableDataFormat(self, array: np.ndarray) -> bool:
        return np.issubdtype(array.dtype, np.floating) or np.issubdtype(array.dtype, np.integer)

    def getSaveFormats(self) -> Sequence[str]:
        return self._SAVE_FORMATS

    def getToFileName(self) -> str:
        return self._TO_FILE

    def _saveTo(self, objectToSave: np.ndarray, location: Path):
        if not self._isSaveableDataShape(objectToSave):
            raise ArrayNotSaveableAsImageError("Array to save needs to be in an appropriate shape. Shape '{}' is not supported.".format(objectToSave.shape))
        
        if not self._isSaveableDataFormat(objectToSave):
            raise ArrayNotSaveableAsImageError("Array to save needs to be of an appropriate data type. Data type '{}' is not supported.".format(objectToSave.dtype))

        # normalize 2D arrays since they could contain any arbitrary data which doesn't necessarily follow any proper image intensity format.
        if len(objectToSave.shape) == 2:
            objectToSave = Normalize()(objectToSave)
        
        imsave(location.as_posix(), img_as_ubyte(objectToSave))

# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(ArrayImageSaveService, savetype = np.ndarray, tofile = ArrayImageSaveService._TO_FILE)