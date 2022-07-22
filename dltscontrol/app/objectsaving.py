"""
Extension which adds object saving and loading services.

Inherit from `SaveService` or from `LoadService` to create custom object save and loading services.

Interfaces
----------
Services: `SaveService` and `LoadService`.

Additional Derivables
---------------------
Components: `ISaveServiceComponent` and `ILoadServiceComponent`. Inherit from those components to get a more convenient way to interact 
with save or load services respectively.
"""

from typing import List, Dict, Type, Union, Sequence, Any, TypeVar, Generic, Optional, Collection
from pathlib import Path

from dltscontrol.tools import PythonConstants
from dltscontrol.apptk import Service, IComponent

import os
import sys

import tkinter as tk

_USE_TK_FILE_BROWSER = False # sys.platform.startswith(PythonConstants.PLATFORM_NAME_LINUX)

if _USE_TK_FILE_BROWSER:
    import tkfilebrowser as tkf
else:
    import tkinter.filedialog as tkf

SAVE_TYPE_KEY = "savetype"
LOAD_TYPE_KEY = "loadtype"

TO_FILE_KEY = "tofile"
FROM_FILE_KEY = "fromfile"

SAVE_COLLECTION_TYPE_KEY = "savecollection"
LOAD_COLLECTION_TYPE_KEY = "loadcollection"

TSaveable = TypeVar("TSaveable")

class UnknownFormatError(Exception):
    """ The supplied file format is not supported. """
    pass

class FileNameDialogAbortedError(Exception):
    """ The file name dialog has been aborted by the user. """
    pass

class SaveService(Service, Generic[TSaveable]):
    """ Service to serialize and save an object. 
    
    A `SaveService` provides an interface to serialize and save an object of an specific type to a specific location. The serialization procedure is not necessarily 
    lossless and the object might be unrestoreable. 
    
    Manifest Properties
    -------------------
    savetype: `Type`
        The type of the object which can be saved. For instance: `savetype = numpy.ndarray`.
    tofile: `str`
        The name of the file type to which the data can be saved. For instance: `tofile = "Binary"` or `tofile = "Image"`.
    savecollection: `Any`
        If specififed the save service may also save collections (list or tuple) which contain objects of the specified savetype.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def isSaveable(self, objectToSave: Union[TSaveable, Collection[TSaveable]]) -> bool:
        """ Returns if the given object can be serialized and saved by the save service. """
        saveType = self.getContext().Application.Manifest.getProperties(self.__class__).get(SAVE_TYPE_KEY, None)
        saveable = saveType is not None

        if saveable: 
            saveable = isinstance(objectToSave, saveType)

            if not saveable and isinstance(objectToSave, (tuple, list)):
                saveable = all(map(lambda item: isinstance(item, saveType), objectToSave))

        return saveable

    def getSaveFormats(self) -> Sequence[str]:
        """ Returns all possible file suffixes/formats which are supported by the save service. """
        raise NotImplementedError

    def getDefaultSaveFormat(self) -> str:
        """ Returns the default save format/suffix of the save service. """
        return next(iter(self.getSaveFormats()))

    def getSaveFormatDescriptions(self) -> Dict[str, str]:
        """ Returns a dictionary in which each or a subset of supported save formats by the save service is mapped to a proper description.
        Example: `{ ".csv": "Comma separated values" }`. """
        return dict()

    def getToFileName(self) -> str:
        """ Returns the name of the file type the save service creates. Should be suitable to fill the following blank 'Save to <ToFileName>' """
        raise NotImplementedError

    def _saveTo(self, objectToSave: Union[TSaveable, Collection[TSaveable]], location: Path):
        """ Finally serializes and saves the objectToSave to the specified location. Any save formats must be denoted by the provided `Path` location. """
        raise NotImplementedError

    def save(self, objectToSave: Union[TSaveable, Collection[TSaveable]], location: Path = None, saveFormat: str = None) -> Path:
        """ Saves the given object to the provided location in the specified format.

        Parameters
        ----------
        objectToSave: `TSaveable`
            The object to be saved.
        location: `Path` (default: `None` -> replaced with the working directory of the application)
            The location to save to. If not specifying a file a file name dialog is opened at the directory of the location.
        saveFormat: `str` (default: `None` -> replaced with the default save format)
            The save format/file suffix of the location to save to. If the location `Path` already has a suffix the save format is ignored.

        Returns
        -------
        location: `Path`
            the final location where the object has been serialized and save to.

        Note
        ----
        If a file name dialog has been opened and gets aborted by the user a `FileNameDialogAbortedError` is raised.
        """
        if location is None:
            location = self.getContext().Application.WorkingDirectory

        if saveFormat is None:
            saveFormat = self.getDefaultSaveFormat()

        if not location.is_dir() and not location.suffixes:
            location = location.with_suffix(saveFormat)

        if location.is_dir() or not location.name or not location.suffixes:
            fileTypes = list()

            saveFormats = self.getSaveFormats()
            saveFormatDescriptions = self.getSaveFormatDescriptions()
            toFileName = self.getToFileName()

            if len(saveFormats) > 1:
                if _USE_TK_FILE_BROWSER:
                    anySaveFormats = "|".join(saveFormats)
                    anySaveFormatsString = "Any {} ({})".format(toFileName, anySaveFormats)
                else:
                    anySaveFormats = saveFormats
                    anySaveFormatsString = "Any {}".format(toFileName)
            
                fileTypes.append((anySaveFormatsString, anySaveFormats))

            for sf in saveFormats:
                if _USE_TK_FILE_BROWSER:
                    saveFormatString = "{} ({})".format(saveFormatDescriptions.get(sf, sf), sf)
                else:
                    saveFormatString = saveFormatDescriptions.get(sf, sf)

                fileTypes.append((saveFormatString, sf))

            title = "Save to {}".format(toFileName)
            initialName = location.name if not location.is_dir() else ""
            initialdir = location.as_posix() if location.is_dir() else os.path.dirname(location)
            
            if _USE_TK_FILE_BROWSER:
                fileName = tkf.asksaveasfilename(initialdir = initialdir, title = title, filetypes = fileTypes, 
                    defaultext = saveFormat, initialfile = initialName)
            else:
                fileName = tkf.asksaveasfilename(initialdir = initialdir, title = title, filetypes = fileTypes, 
                    defaultextension = saveFormat, initialfile = initialName, parent = self.getContext().getTk())

            if fileName:
                location = Path(fileName)
            else:
                raise FileNameDialogAbortedError("File name dialog has been aborted. Can't save an object without a valid location.")
        
        saveFormat = "".join(location.suffixes)

        if saveFormat not in self.getSaveFormats():
            raise UnknownFormatError("Can't save object in unknown format '{}'. Supported formats: {}.".format(saveFormat, self.getSaveFormats()))

        self._saveTo(objectToSave, location)

        return location

TLoadable = TypeVar("TLoadable")

class LoadService(Service, Generic[TLoadable]):
    """ Service to load a saved and serialized object. 
    
    A `LoadService` provides an interface to load a serialized object of a specific type from a specific location.  
    
    Manifest Properties
    -------------------
    loadtype: `Type`
        The type of the object which can be loaded. For instance: `loadtype = numpy.ndarray`.
    fromfile: `str`
        The name of the file type from which the data can be loaded. For instance: `fromfile = "Binary"` or `fromfile = "Json"`.
    loadcollection: `Type`
        If specififed the load service may also load collections (list or tuple) which contain objects of the specified loadtype.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def isLoadable(self, location: Path) -> bool:
        """ Returns if the specified location could contain a loadable serialed object. """
        return "".join(location.suffixes) in self.getLoadFormats() and location.exists()

    def getLoadFormats(self) -> Sequence[str]:
        """ Returns all possible file suffixes/formats which are supported by the load service. """
        raise NotImplementedError

    def getLoadFormatDescriptions(self) -> Dict[str, str]:
        """ Returns a dictionary in which each or a subset of supported load formats by the load service is mapped to a proper description.
        Example: `{ ".csv": "Comma separated values" }`. """
        return dict()

    def getFromFileName(self) -> str:
        """ Returns the name of the file type from which the load service loads the object. Should be suitable to fill the following blank 'Load from <FromFileName>' """
        raise NotImplementedError
    
    def _loadFrom(self, location: Path) -> Union[TLoadable, Collection[TLoadable]]:
        """ Finally loads and deserializes the loadable object from the given location which must exist and include a loadable load format/file suffix. """
        raise NotImplementedError

    def load(self, location: Path = None) -> Union[TLoadable, Collection[TLoadable]]:
        """ Loads a serialized object from the provided location in the specified format.

        Parameters
        ----------
        location: `Path` (default: `None` -> replaced with the working directory of the application)
            The location to load from. If not specifying a file a file name dialog is opened at the directory of the location.

        Returns
        -------
        loadedObject: `TLoadable`
            The deserialized object from the file.

        Note
        ----
        If a file name dialog has been opened and gets aborted by the user a `FileNameDialogAbortedError` is raised.
        """
        if location is None:
            location = self.getContext().Application.WorkingDirectory

        if not location.name or not location.suffixes:
            fileTypes = list()

            loadFormats = self.getLoadFormats()
            loadFormatDescriptions = self.getLoadFormatDescriptions()
            fromFileName = self.getFromFileName()

            if len(loadFormats) > 1:
                if _USE_TK_FILE_BROWSER:
                    anyLoadFormats = "|".join(loadFormats)
                    anyLoadFormatsString = "Any {} ({})".format(fromFileName, anyLoadFormats)
                else:
                    anyLoadFormats = loadFormats
                    anyLoadFormatsString = "Any {}".format(fromFileName)

                fileTypes.append((anyLoadFormatsString, anyLoadFormats))

            for loadFormat in loadFormats:
                if _USE_TK_FILE_BROWSER:
                    loadFormatString = "{} ({})".format(loadFormatDescriptions.get(loadFormat, loadFormat), loadFormat)
                else:
                    loadFormatString = loadFormatDescriptions.get(loadFormat, loadFormat)

                fileTypes.append((loadFormatString, loadFormat))

            initialdir = location.as_posix() if location.is_dir() else os.path.dirname(location)

            if _USE_TK_FILE_BROWSER:
                fileName = tkf.askopenfilename(initialdir = initialdir, title = "Load from {}".format(fromFileName), filetypes = fileTypes)
            else:
                fileName = tkf.askopenfilename(initialdir = initialdir, title = "Load from {}".format(fromFileName), 
                    filetypes = fileTypes, parent = self.getContext().getTk())

            if fileName:
                location = Path(fileName)
            else:
                raise FileNameDialogAbortedError("File name dialog has been aborted. Can't load an object without a valid location.")
        
        loadFormat = "".join(location.suffixes)

        if loadFormat not in self.getLoadFormats():
            raise UnknownFormatError("Can't load object from unknown format '{}'. Supported formats: {}.".format(loadFormat, self.getLoadFormats()))

        loadedObject = self._loadFrom(location)

        return loadedObject

class ISaveServiceComponent(IComponent):
    """ Helper Component which provides convenient methods to interact with `SaveService`s. """

    def requestSaveService(self, saveType: Type, toFileName: str = None, serviceName: str = None) -> SaveService:
        """ Requests a `SaveService` of the specified properties in the component's local context. 
        
        Parameters
        ----------
        saveType: `Type`
            The savetype under which the save service must have been registered into the manifest. Can be a subclass of the actual registered type.
        toFileName: `str` (default: `None`)
            The tofile under which the save service must have been registered into the manifest. If `None` it's ignored.
        serviceName: `str` (default: `None`)
            The name under which the save service must have been registered into the manifest. If `None` it's ignored.
        
        Returns
        -------
        saveService: `SaveService`
            The requested save service.
        """
        saveServiceClasses = self.getSaveServiceClassesForType(saveType, serviceName)

        if toFileName:
            saveServiceClasses = filter(lambda serviceClass: toFileName == self.getToFileName(serviceClass), saveServiceClasses)

        return self.getComponentContext().requestService(next(iter(saveServiceClasses), None))

    def getToFileName(self, saveServiceClass: Type[SaveService]) -> Optional[str]:
        """ Returns the tofile property under which the specified save service class has been registered into the manifest. """
        return self.getContext().Application.Manifest.getProperties(saveServiceClass).get(TO_FILE_KEY, None)

    def getToFileNamesForType(self, saveType: Type) -> List[str]:
        """ Returns the tofile properties of all save services which have been registered under the given savetype or a parent class of it. """
        toFileNames = list()

        for saveServiceClass in self.getSaveServiceClassesForType(saveType):
            toFileName = self.getToFileName(saveServiceClass)

            if toFileName:
                toFileNames.append(toFileName)
        
        return toFileNames

    def isCollectionSavable(self, saveServiceClass: Type[SaveService]) -> bool:
        """ Returns the whether the specified save service is able to save collections of its savetype. """
        return SAVE_COLLECTION_TYPE_KEY in self.getContext().Application.Manifest.getProperties(saveServiceClass)

    def getSaveServiceClassesForType(self, saveType: Type, serviceName: str = None) -> List[SaveService]:
        """ Returns all save service classes which have been registered under the given savetype or a parent class of it and the given name. """
        saveServiceClasses = list()

        for serviceClass in self.getContext().Application.Manifest.getComponentClasses(SaveService, serviceName):

            serviceSaveType = self.getContext().Application.Manifest.getProperties(serviceClass).get(SAVE_TYPE_KEY, None)

            if serviceSaveType is not None and issubclass(saveType, serviceSaveType):
                saveServiceClasses.append(serviceClass)
        
        return saveServiceClasses

class ILoadServiceComponent(IComponent):
    """ Helper Component which provides convenient methods to interact with `LoadService`s. """

    def requestLoadService(self, loadType: Type, fromFileName: str = None, serviceName: str = None) -> LoadService:
        """ Requests a `LoadService` of the specified properties in the component's local context. 
        
        Parameters
        ----------
        loadType: `Type`
            The loadtype under which the load service must have been registered into the manifest. Can be a parent class of the actual registered type.
        fromFileName: `str` (default: `None`)
            The fromfile under which the load service must have been registered into the manifest. If `None` it's ignored.
        serviceName: `str` (default: `None`)
            The name under which the load service must have been registered into the manifest. If `None` it's ignored.
        
        Returns
        -------
        loadService: `SaveService`
            The requested load service.
        """
        loadServiceClasses = self.getLoadServiceClassesForType(loadType, serviceName)

        if fromFileName:
            loadServiceClasses = filter(lambda serviceClass: fromFileName == self.getFromFileName(serviceClass), loadServiceClasses)

        return self.getComponentContext().requestService(next(iter(loadServiceClasses), None))

    def getFromFileName(self, loadServiceClass: Type[LoadService]) -> Optional[str]:
        """ Returns the fromfile property under which the specified load service class has been registered into the manifest. """
        return self.getContext().Application.Manifest.getProperties(loadServiceClass).get(FROM_FILE_KEY, None)

    def getFromFileNamesForType(self, loadType: Type) -> List[str]:
        """ Returns the fromfile properties of all load services which have been registered under the given loadtype or a subclass of it. """
        fromFileNames = list()

        for loadServiceClass in self.getLoadServiceClassesForType(loadType):
            fromFileName = self.getFromFileName(loadServiceClass)

            if fromFileName:
                fromFileNames.append(fromFileName)
        
        return fromFileNames

    def isCollectionLoadable(self, loadServiceClass: Type[LoadService]) -> bool:
        """ Returns the whether the specified load service is able to load collections of its loadtype. """
        return LOAD_COLLECTION_TYPE_KEY in self.getContext().Application.Manifest.getProperties(loadServiceClass)

    def getLoadServiceClassesForType(self, loadType: Type, serviceName: str = None) -> List[LoadService]:
        """ Returns all load service classes which have been registered under the given loadtype or a subclass of it and the given name. """
        loadServiceClasses = list()

        for serviceClass in self.getContext().Application.Manifest.getComponentClasses(LoadService, serviceName):

            serviceLoadType = self.getContext().Application.Manifest.getProperties(serviceClass).get(LOAD_TYPE_KEY, None)

            if serviceLoadType is not None and issubclass(serviceLoadType, loadType):
                loadServiceClasses.append(serviceClass)
        
        return loadServiceClasses