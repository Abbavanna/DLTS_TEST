""" 
Rudimentary application model framework based on `tkinter`.

This module is used to create `tkinter` based applications with several windows. `Applet`s represent the main windows, 
`Dialog`s short term interaction windows, `Panel`s parts of a window and `Service`s interfaces for application wide shared resources.
All `Component` classes (`Applet`s, `Dialog`s, ...) of an application have to be inserted into an `ApplicationManifest` which passed to
an `Application` on startup.

Classes
-------
The only classes from which to inherit from are `Applet`, `Service`, `Dialog` and `Panel`.

Example
-------
The following code creates an application consisitng of a single empty applet/window which is shown on application startup.

>>> MyApplet(Applet):
>>>     pass
>>> manifest = ApplicationManifest()
>>> manifest.insert(MyApplet, root = True, start = True)
>>> workingDirectory = getWorkingDirectory() # user provided function which returns a `Path`
>>> Application(manifest, workingDirectory).run()
"""

from pathlib import Path
from typing import Dict, OrderedDict, List, Iterable, Type, Tuple, Any, Sequence, Union
from collections import OrderedDict

from dltscontrol.tools import PythonConstants

import sys
import logging

import tkinter as tk
import tkinter as ttk
import tkinter.messagebox as tkm

import dltscontrol.tkext as tkext

COMPONENT_PROPERTY_NAMES = "name"
COMPONENT_PROPERTY_DISPLAY_NAME = "displayname"
COMPONENT_PROPERTY_GLOBAL = "_global"

COMPONENT_DEFAULT_PROPERTIES = {COMPONENT_PROPERTY_GLOBAL: False, COMPONENT_PROPERTY_DISPLAY_NAME: "Component"}

APPLET_PROPERTY_MULTIPLE_INSTANCES = "multiple"
APPLET_PROPERTY_MENU_ENTRY_NAME = "entry"
APPLET_PROPERTY_ADD_TO_MENU = "menu"
APPLET_PROPERTY_START_ON_APP_START = "start"
APPLET_PROPERTY_ROOT = "root"
APPLET_PROPERTY_APPMENU = "appmenu"

APPLET_DEFAULT_PROPERTIES = {APPLET_PROPERTY_MENU_ENTRY_NAME: "Applet Entry", APPLET_PROPERTY_MULTIPLE_INSTANCES: False, 
    APPLET_PROPERTY_ADD_TO_MENU: True, APPLET_PROPERTY_START_ON_APP_START: False, APPLET_PROPERTY_ROOT: False, APPLET_PROPERTY_APPMENU: True}

SERVICE_PROPERTY_MULTIPLE_INSTANCES = "multiple"

SERVICE_DEFAULT_PROPERTIES = {SERVICE_PROPERTY_MULTIPLE_INSTANCES: False}

APPLET_MENU_NAME = "App"
APPLET_MENU_ENTRY_QUIT = "Quit"

logger = logging.getLogger("apptk")

class AppTkException(Exception):
    """ The base exception of the apptk module. """
    pass

class ApplicationManifestError(AppTkException):
    """ Exception related to application manifest failures. """
    pass

class ApplicationManifest:
    """ Defines the application components an application consists of.

    All `Component` classes which are part of the application have to be inserted in this manifest in order to use them at application runtime.
    Insertation during application runtime is supported as well to insert components 'hiddenly'.
    """

    def __init__(self):
        self._components: Dict[Type, Dict[str, Any]] = OrderedDict()

    @property
    def Components(self) -> Iterable[Tuple[Type, Dict]]:
        """ All component-properties combinations. """
        return self._components.items()

    def getComponents(self, componentInterface) -> Iterable[Tuple[Type, Dict[str, Any]]]:
        """ Returns an `Iterable` of all component-properties combinations where the component is a subclass of the given component interface. """
        return filter(lambda componentTuple: issubclass(componentTuple[0], componentInterface), self.Components)

    def getComponentsList(self, componentInterface) -> List[Tuple[Type, Dict[str, Any]]]:
        """ Same as `ApplicationManifest.getComponents` but returns a `List` instead of an `Iterable`. """
        return list(filter(lambda componentTuple: issubclass(componentTuple[0], componentInterface), self.Components))

    def getComponent(self, componentInterface) -> Tuple[Type, Dict[str, Any]]:
        """ Returns the first element or `None` of `ApplicationManifest.getComponentsList`. """
        return next(self.getComponents(componentInterface), None)
    
    @property
    def ComponentClasses(self) -> Iterable[Type]:
        """ All component classes. """
        return self._components.keys()

    def getComponentClasses(self, componentInterface: Type, name: str = None) -> List[Type]:
        """ Returns a `List` containing all component classes which implement the given component interface. 
        If the given name is not `None` the component classes also had to be inserted with the specified name. """
        classes = list()
        for componentClass in self.ComponentClasses:
            if issubclass(componentClass, componentInterface):
                properties = self.getProperties(componentClass)

                if name is None or COMPONENT_PROPERTY_NAMES in properties.keys() and name in properties[COMPONENT_PROPERTY_NAMES]:
                    classes.append(componentClass)
        return classes

    def getComponentClass(self, componentInterface: Type, name: str = None) -> Type:
        """ Returns the first element or `None` of `ApplicationManifest.getComponentClasses`. """
        return next(iter(self.getComponentClasses(componentInterface, name)), None)

    @property
    def Applets(self) -> Iterable[Tuple[Type, Dict]]:
        """ All applet-properties combinations. """
        return self.getComponents(Applet)
    
    @property
    def AppletClasses(self) -> List[Type]:
        """ All applet. """
        return self.getComponentClasses(Applet)

    @property
    def Services(self) -> Iterable[Tuple[Type, Dict]]:
        """ All service-properties combinations. """
        return self.getComponents(Service)

    @property
    def ServiceClasses(self) -> List[Type]:
        """ All service. """
        return self.getComponentClasses(Service)
    
    @property
    def Dialogs(self) -> Iterable[Tuple[Type, Dict]]:
        """ All dialog-properties combinations. """
        return self.getComponents(Dialog)

    @property
    def DialogClasses(self) -> List[Type]:
        """ All dialog. """
        return self.getComponentClasses(Dialog)

    @property
    def Panels(self) -> Iterable[Tuple[Type, Dict]]:
        """ All panel-properties combinations. """
        return self.getComponents(Panel)

    @property
    def PanelClasses(self) -> List[Type]:
        """ All panels. """
        return self.getComponentClasses(Panel)

    def isAvailable(self, componentInterface: Type, name: str = None) -> bool:
        """ Returns if there is a component which implements the given interface and has the given name. """
        return self.getComponentClass(componentInterface, name) is not None

    def isUniquelyAvailable(self, componentInterface: Type, name: str = None) -> bool:
        """ Returns if there is only one component which implements the given interface and has the given name. """
        return len(self.getComponentClasses(componentInterface, name)) == 1

    def insert(self, componentClass: Type, *names: Sequence[str], **componentProperties):
        """ Inserts a new component into or updates an existing component of the manifest.
        
        Parameters
        ----------
        names: `Sequence[str]` (default: `[]`)
            the names under which the component should be registered, may be empty
        componentProperties: `Dict` (The default properties are component dependent)
            the properties under which the component should be registered, may include custom key-value pairs
        
        Component Properties
        --------------------
        _global: `bool` (default: `False`), ignored for dialogs and panels
            Global components can only exist in the application's context but not in any sub context. 
            Request for global components are redirected to the application's context. 
        displayname: `str` (default: `"Component"`)
            A descriptive name of the component
        multiple: bool (default: `False`), service and applet only
            Whether there should be created a new or queried an existing applet or service on applet-start or service-request respectively.
        menu: bool (default: `True`), applet only:
            Whether to be startable from the applet app menu or not.
        entry: str (default: "Applet Entry"), applet only
            The displayed text of the entry in the applet app menu. 
        start: bool (default: `False`), applet only
            Whether the applet shall be started on app startup or not.
        root: bool (default: `False`), applet only
            Wheter the applet keeps the application alive or not. If all "root-applets" are closed the application will shutdown automatically.
        appmenu: bool (default: `True`), applet only
            Whether the applet shall display the app menu in its menubar or not.
        """
        if not issubclass(componentClass, Component):
            raise ApplicationManifestError("Can't insert class '{0}' since it's not of required type '{1}'.".format(componentClass, Component))
        
        properties = dict() if componentClass not in self._components else self._components[componentClass]

        if not properties:
            properties.update(COMPONENT_DEFAULT_PROPERTIES)

            if issubclass(componentClass, Applet):
                properties.update(APPLET_DEFAULT_PROPERTIES)
            elif issubclass(componentClass, Service):
                properties.update(SERVICE_DEFAULT_PROPERTIES)

        if names:
            properties[COMPONENT_PROPERTY_NAMES] = names

        if componentProperties:
            for propertyKey, propertyValue in componentProperties.items():
                properties[propertyKey] = propertyValue
                
        self._components[componentClass] = properties

    def getProperties(self, componentClass: Type) -> Dict[str, Any]:
        """ Returns the properties of the given component. Raises an exception if the component is not available. """

        if componentClass not in self._components.keys():
            raise ApplicationManifestError("Can't retrieve the configuration of unknown component '{0}'.".format(componentClass))
            
        return self._components[componentClass]

    def getNames(self, componentClass: Type) -> Sequence[str]:
        """ Returns the names under which the given component has been inserted. If there are no names `None` is returned. """
        config = self.getProperties(componentClass)
        return config.get(COMPONENT_PROPERTY_NAMES, None)

class ITkBound:
    """ Base interface of all classes connected/bound to a tkinter widget. 
    
    This class should share the same lifecyle as the bound tkinter widget.
    Like it should be unusable, disposed or have cleaned up his resources if the corresponding tkinter widget has been destroyed."""
    
    def getTk(self) -> tk.Widget:
        """ Returns the tkinter widget to which and whose lifecyle the `ITkBound` object is bound to.. """
        raise NotImplementedError

def showerror(function):
    """ Decorator which displays and logs an error message box if an exception occurs during execution of the decorated function. """       
    def safeFunction(self, *args, **kwargs):
        try:
            function(self, *args, **kwargs)
        except Exception as ex:
            parent = None
            if isinstance(self, ITkBound):
                parent = self.getTk()
            elif isinstance(self, Component):
                parent = self.getContext().getTk()
            logger.exception(ex)
            tkm.showerror("Error: {0}".format(ex.__class__.__name__), ex, parent = parent)

    return safeFunction

class ApplicationRunError(AppTkException):
    """ Exception related to application run failures. """
    pass

class Application(ITkBound):
    """ Represents an application based on the apptk module. 

    An application is bound to a `tkinter.Tk` object which is the root of all other tkinter widgets and whose window isn't going to be shown on screen. 
    It always needs an `ApplicationManifest` and a working directory (Usually the directory where the application has been started). An icon file can
    be provided optionally. An application holds an `ApplicationContext` which is the base context of all other contexts and is also bound to the 
    `tkinter.Tk` root. As soon as an application object has been created the application can be started with `Application.run`.
    """
    def __init__(self, applicationManifest: ApplicationManifest, workingDirectory: Path, iconFile: Path = None):
        self._applicationManifest = applicationManifest
        self._workingDirectory = workingDirectory

        self._tkRoot: tk.Tk = None
        self._context = None
        self._iconFile = iconFile

    def getTk(self) -> tk.Tk:
        """ The tkinter root object. """
        return self._tkRoot

    @property
    def IsRunning(self) -> bool:
        """ Whether the application is running or not. """
        return self._tkRoot is not None

    @property
    def WorkingDirectory(self) -> Path:
        """ The working directory of the application. """
        return self._workingDirectory

    @property
    def IconFilePath(self) -> Path:
        """ The path to the application's icon. """
        return self._iconFile

    @property
    def Manifest(self) -> ApplicationManifest:
        """ Returns the application's manifest. """
        return self._applicationManifest

    @property
    def Context(self):
        """ The root/application context. """
        return self._context

    def run(self):
        """ Starts the application. Throws an exception if the application has already been started. """
        if self.IsRunning:
            raise ApplicationRunError("App is already running.")

        self._tkRoot = tk.Tk()
        self._tkRoot.withdraw()

        if PythonConstants.PLATFORM_NAME_WINDOWS == sys.platform and self._iconFile is not None and self._iconFile.exists():
            try:
                self._tkRoot.iconbitmap(default = self._iconFile.as_posix())
            except Exception as ex:
                logger.exception("Provided icon file could not be applied as default window icon. Reason: %s", ex)

        self._context = ApplicationContext(self)
        
        for componentClass, config in self._applicationManifest.Applets:
            if config.get(APPLET_PROPERTY_START_ON_APP_START, APPLET_DEFAULT_PROPERTIES[APPLET_PROPERTY_START_ON_APP_START]):
                try:
                    self._context.startApplet(componentClass)
                except Exception as ex:
                    logger.exception(ex)
                
        if tuple(self._context._Applets):
            self._tkRoot.mainloop()
        else:
            logger.error("No applet has been started. The application can't run without any working start-applet.")

    def quit(self):
        """ Quits the application and destroys the tkinter root object. """
        if self._tkRoot is not None:
            # prevent another successful call of this method as soon as all root-applets have been destroyed
            tkRoot = self._tkRoot
            self._tkRoot = None
            tkRoot.destroy()

class ComponentAvailabilityException(AppTkException):
    """ Base exception for errors regarding components which could not be requested or found. """
    pass

class ComponentRequestAbortedError(ComponentAvailabilityException):
    """ Component request has been aborted by some user action. """
    pass

class ComponentNotOfRequiredTypeError(ComponentAvailabilityException):
    """ Component is not of required type. """
    pass

class ComponentNotFoundError(ComponentAvailabilityException):
    """ Component of specified properties has not been found. It might be no part of the application and hasn't been registered in the application's manifest. """
    pass

class Context(ITkBound):
    """ Holds, creates and gives acccess to all application components. Those are applets, services and dialogs. 
    
    A context is used to start applets, request services and open dialogs. Additionally it provides access to the `Application`, thus to the `ApplicationManifest` 
    and to all components contained by the context. All application components created in this context are bound to its lifecycle, which means if the context gets 
    destroyed all components of it are going to be destroyed as well. 
    """

    def __init__(self, tkBond):
        self._tkBond = tkBond
        self._components: List[Component] = list()

    @property
    def Application(self) -> Application:
        """ Returns the application. """
        raise NotImplementedError 

    def getTk(self) -> tk.Widget:
        """ Returns the tkinter widget the context is bound to. """
        return self._tkBond
    
    @property
    def _Applets(self) -> Iterable:
        """ All created applets in this context. """
        return filter(lambda component: isinstance(component, Applet), self._components)

    @property
    def _Services(self) -> Iterable:
        """ All started services in this context. """
        return filter(lambda component: isinstance(component, Service), self._components)
    
    def _onComponentDestroy(self, event, component):
        """ Called when a contained component of the context gets destroyed. """
        if event.widget is component.getTk() and component in self._components:
            self._components.remove(component)

    def _determineComponentClass(self, interface: Type, name: str = None, askSelection: bool = True, preferExisting: bool = True):
        """ Determines the component class which has been registered in the application's manifest under the given name and implements the given interface. 
        
        Parameters
        ----------
        interface: `Type`
            The interface the component has to be an instance of.
        name: `str` (default: `None`)
            The name the component has been given to. If `None` it's ignored.
        askSelection: `bool` (default: `True`)
            Whether to open a selection dialog if multiple matching classes are found or to take the one founf first.
        preferExisting: `bool` (default: `True`)
            Whether to check the classes of exisiting components first and skip the manifest if one has been found or to start directly searching the application's manifest.
        
        Returns
        -------
        componentClass: `Type`
            The found and/or selected component class for the given interface and name.
        """
        if preferExisting:
            components = list(filter(
                lambda component: 
                    isinstance(component, interface) and self.Application.Manifest.isAvailable(type(component), name), 
                self._components))
        else:
            components = None
        
        if components:
            componentClasses = list()

            for component in components:
                componentClass = type(component)
                if componentClass not in componentClasses:
                    componentClasses.append(componentClass)
        else:
            componentClasses = self.Application.Manifest.getComponentClasses(interface, name)

        if not componentClasses:
            raise ComponentNotFoundError("Can't find any components for interface '{}' and name '{}'.".format(interface, name)) 

        if askSelection and len(componentClasses) > 1:
            componentClasses = tkext.askSelection(self.getTk(), *componentClasses, converter = lambda componentClass: componentClass.__name__, allowNone = False,
                title = "Select '{0}'".format(interface.__name__))

        return next(iter(componentClasses))

    def startApplet(self, appletInterface: Type, appletName: str = None, askSelection = True, **startProperties):
        """ Starts and returns an `Applet` with the given startProperties and for the given interface and name. Creates an new one if needed.

        This method is used to start applets which are registered in the application's manifest. If the applet allows multiple instances or
        hasn't been created yet a new applet will be created, otherwise the existing will be started again. As soon as the applet is started 
        the applet is shown on screen. If any exceptions occur during applet start or creation the applet is considered as not working and 
        will be closed immediatly. If the applet start succeeds the started applet becomes part of this context if it not already is.

        Parameters
        ----------
        appletInterface: `Type` 
            the type the applet to start has to implement.
        appletName: `str` (default: `None`)
            The name under which the applet should be registered. If `None` the name under which the applet was registered is ignored.
        askSelection: `bool` (default: `True`)
            Whether to open a selection dialog if multiple matching applet classes are found or to take the one found first.
        startProperties: `Dict` (default: `{}`)
            The properties to be passed to the applet on start.

        Returns
        -------     
        applet: `Applet` 
            The started applet if succeeded.
        """
        appletClass = self._determineComponentClass(appletInterface, appletName, askSelection)
        applet = None

        if appletClass is not None and issubclass(appletClass, Applet):
            appletProperties = self.Application.Manifest.getProperties(appletClass)
            applet = next(filter(lambda applet: isinstance(applet, appletClass), self._Applets), None)

            if applet is None and appletProperties.get(COMPONENT_PROPERTY_GLOBAL) and not self is self.Application.Context:
                applet = self.Application.Context.startApplet(appletInterface, appletName, askSelection, **startProperties)
            else:
                if applet is None or appletProperties.get(APPLET_PROPERTY_MULTIPLE_INSTANCES, APPLET_DEFAULT_PROPERTIES[APPLET_PROPERTY_MULTIPLE_INSTANCES]):
                    applet = appletClass(self.getTk(), self)
                    applet.getTk().bind(tkext.TK_EVENT_DESTROY, lambda event, applet = applet: self._onComponentDestroy(event, applet), tkext.TK_EVENT_BIND_ADD)
                
                try:
                    applet.onStart(**startProperties)

                    if applet not in self._components:
                        self._components.append(applet)
                except Exception as ex:
                    applet.close()
                    raise ex
        else:
            raise ComponentNotOfRequiredTypeError("Found class '{}' for applet interface '{}' and name '{}' but it's not of required class '{}'."
                .format(appletClass, appletInterface, appletName, Applet))

        return applet

    def isAppletRunning(self, appletInterface: Type, appletName: str = None) -> bool:
        """ Returns if there is any running applet which implements the given applet interface and has the given name. """
        return self._getApplet(appletInterface, appletName) is not None

    def requestService(self, serviceInterface: Type, serviceName: str = None, askSelection = True, **requestProperties):
        """ Requests and returns a service with the given requestProperties and for the given interface and properties. Creates a new service instance if needed. 
        
        This method is used to request services which are registered in the application's manifest. If the service allows multiple instances or
        hasn't been started yet a new service will be started, otherwise the existing will be requested again. If any exceptions occur during service request 
        or start the service is considered as not working and will be destroyed immediatly. If the service request succeeds the service becomes part of this context 
        if it not already is.
        
        Parameters
        ----------
        serviceInterface: `Type` 
            The type the requested service has to implement.
        serviceName: `str` (default: `None`)
            The name under which the service should be registered. If `None` the name under which the service was registered is ignored.
        askSelection: `bool` (default: `True`)
            Whether to open a selection dialog if multiple matching service classes are found or to take the one found first.
        requestProperties: `Dict` (default: `{}`)
            The request properties to be passed to the service.
        
        Returns
        -------
        service: `Service` 
            The requested service if succeeded.
        """
        serviceClass = self._determineComponentClass(serviceInterface, serviceName, askSelection)
        service = None
        
        if serviceClass is not None and issubclass(serviceClass, Service):
            serviceProperties = self.Application.Manifest.getProperties(serviceClass)
            service = next(filter(lambda service: isinstance(service, serviceClass), self._Services), None)
            
            if service is None and serviceProperties.get(COMPONENT_PROPERTY_GLOBAL) and not self is self.Application.Context:
                service = self.Application.Context.requestService(serviceInterface, serviceName, askSelection, **requestProperties)
            else:
                if service is None or serviceProperties.get(SERVICE_PROPERTY_MULTIPLE_INSTANCES, SERVICE_DEFAULT_PROPERTIES[SERVICE_PROPERTY_MULTIPLE_INSTANCES]):
                    service = serviceClass(self.getTk(), self)
                    service.getTk().bind(tkext.TK_EVENT_DESTROY, lambda event, service = service: self._onComponentDestroy(event, service), tkext.TK_EVENT_BIND_ADD)
                
                try:
                    service.onRequest(**requestProperties)

                    if service not in self._components:
                        self._components.append(service)
                except Exception as ex:
                    service.stop()
                    raise ex
        else:
            raise ComponentNotOfRequiredTypeError("Found class '{}' for service interface '{}' and name '{}' but it's not of required class '{}'."
                .format(serviceClass, serviceInterface, serviceName, Service))

        return service

    def requestAllServices(self, serviceInterface: Type, serviceName: str = None, **requestProperties) -> List:
        """ Requests all services which implement the given interface and are registered under the given name. See `Context.requestService`. """
        serviceClasses = self.Application.Manifest.getComponentClasses(serviceInterface, serviceName)
        services = list()

        for serviceClass in serviceClasses:
            service = self.requestService(serviceClass, serviceName, **requestProperties)

            if service is not None:
                services.append(service)
        
        return services

    def stopService(self, serviceInterface: Type, serviceName: str = None):
        """ Destroys all services of the given service interface and name and removes them from the context. """ 
        for service in self._getServices(serviceInterface, serviceName):
            service.stop() 

    def isServiceRunning(self, serviceInterface: Type, serviceName: str = None):
        """ Returns if there is any running service which implements the given service interface and has the given name. """
        return self._getService(serviceInterface, serviceName) is not None
    
    def openDialog(self, dialogInterface: Type, dialogName: str = None):
        """ Opens and returns a dialog window for the given interface and name if it's registered in the application's manifest. 
        
        This method is used to open and show dialogs which are registered in the application's manifest. Dialogs are always "freshly" created. 
        Dialogs which already have been opened and are part of the context can't be opened again. Usually a dialog gains all the users attention 
        and blocks all other GUI components as soon as it is created and will be destroyed and removed from the context when the users 
        finishes interacting with the dialog. If the dialog creation fails the dialog is considered broken and will be closed immediatly. The
        opened dialog class is going to be the first which has been found in the application's manifest and matches the given criteria.

        Parameters
        ----------
        dialogInterface: `Type`
            The dialog interface the dialog has to implement.
        dialogName: `str` (default: `None`)
            The name under which the dialog has to be registered. If `None` the name under which the dialog was registered is ignored.
        
        Returns
        -------
        dialog: `Dialog`
            The opened dialog if succeeded.
        """
        dialogClass = self.Application.Manifest.getComponentClass(dialogInterface, dialogName)
        dialog = None

        if dialogClass is not None and issubclass(dialogClass, Dialog):
            dialog = dialogClass(self.getTk(), self)
            dialog.getTk().bind(tkext.TK_EVENT_DESTROY, lambda event, dialog = dialog: self._onComponentDestroy(event, dialog), tkext.TK_EVENT_BIND_ADD)
            self._components.append(dialog)
        else:
            raise ComponentNotOfRequiredTypeError("Found class '{}' for dialog interface '{}' and name '{}' but it's not of required class '{}'."
                .format(dialogClass, dialogInterface, dialogName, Dialog))

        return dialog

    def _getServices(self, serviceInterface: Type, serviceName: str = None) -> Iterable:
        """ Returns all services which are currently part of the context and implement the given service interface and have the given name. No service request is made. """
        return filter(lambda service: isinstance(service, serviceInterface) and (serviceName is None or self.Application.Manifest.isAvailable(type(service), serviceName)), self._Services)
    
    def _getService(self, serviceInterface: Type, serviceName: str = None):
        """ Returns the first found service which is part of the context and implements the given service interface and has the given name. """
        return next(self._getServices(serviceInterface, serviceName), None)
       
    def _getApplets(self, appletInterface: Type, appletName: str = None) -> Iterable:
        """ Returns all applets which are currently part of the context and implement the given applet interface and have the given name. No applet start is made. """
        return filter(lambda applet: isinstance(applet, appletInterface) and (appletName is None or self.Application.Manifest.isAvailable(type(applet), appletName)), self._Applets)
    
    def _getApplet(self, appletInterface: Type, appletName: str = None):
        """ Returns the first found applet which is part of the context and implements the given applet interface and has the given name. """
        return next(self._getApplets(appletInterface, appletName), None)

class ApplicationContext(Context):
    """ Context of the application. Shall only be created by a `Application`. Highest/Toplevel Context. """

    def __init__(self, application: Application):
        super().__init__(application.getTk())
        
        self._application = application

    @property
    def Application(self) -> Application:
        return self._application
       
    def _onComponentDestroy(self, event, applet):
        super()._onComponentDestroy(event, applet)
        
        # shut application down if no root-applets are present anymore
        if next(filter(lambda applet: self.Application.Manifest.getProperties(applet.__class__)[APPLET_PROPERTY_ROOT], self._Applets), None) is None:
            self.Application.quit()

class SubContextCreationError(AppTkException):
    """ Exception related to errors during creation of a `SubContext`. """
    pass

class SubContext(Context):
    """ Context to allow the creation of application components which are bound to a different context lifecycle than the application context's lifecycle. """

    def __init__(self, tkBond: tk.Widget, parentContext: Context):
        super().__init__(tkBond)

        if tkBond not in parentContext.getTk().winfo_children():
            raise SubContextCreationError("Can't create a sub context whose tkinter bond is not child of the parent context's tkinter bond.")
        
        self._parentContext = parentContext

    @property
    def Application(self) -> Application:
        return self._parentContext.Application

class RequirementError(AppTkException):
    """ Exception related to component requirements. """
    pass

class IComponent(ITkBound):
    """ Application component interface implemented by all application components. 
    
    Application components are bound to and share a tkinter widget's lifecycle and are contained in a certain context. Application components have their own
    component context which allows them to start applets, open dialogs, request services "privately" and bound to their own tkinter bond and thus its lifecycle."""

    def getContext(self) -> Context:
        """ Returns the context which contains the component. """
        raise NotImplementedError
    
    def getComponentContext(self) -> Context:
        """ Returns the local context owned by the component. """
        raise NotImplementedError

    def require(self, componentClass: Type, componentName: str = None):
        """ Throws an exception if the given component class isn't inserted into the application's manifest under the given name. 
        If the name is `None` it is ignored. """
        if not self.getContext().Application.Manifest.isAvailable(componentClass, componentName):
            raise RequirementError("Component '{0}' requires component '{1}' to function properly.".format(self.__class__, componentClass))

class Component(IComponent):
    """ Abstract application component base class. 
    
    Parameters
    ----------
    tkMaster: `tkinter.Widget`
        The parent tkinter widget of the component and its tkinter bond.
    """
    def __init__(self, tkMaster: tk.Widget, context: Context):
        self._tkBond = self._createTkBond(tkMaster)
        self._context = context

        self.getTk().bind(tkext.TK_EVENT_DESTROY, lambda event: self.onDestroy(event) if event.widget is self._tkBond else None, tkext.TK_EVENT_BIND_ADD)
        self.getTk().after_idle(self.onCreate)

    def getContext(self) -> Context:
        return self._context

    def getTk(self) -> tk.Widget:
        return self._tkBond

    def onCreate(self):
        """ Called when the bound tkinter widget has been created. """
        pass

    def onDestroy(self, event):
        """ Called when the bound tk widget is about to get destroyed inevitably. """
        pass

    def _createTkBond(self, tkMaster: tk.Widget) -> tk.Widget:
        """ Creates the tkinter widget to which and whose lifecycle the component is bound to. """
        raise NotImplementedError

class GraphicalComponent(Component):
    """ Abstract application component which a represents a tkinter widget which is actually shown on screen. """
    
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._focus = False
        self._mouseEntered = False
       
        self.getTk().bind(tkext.TK_EVENT_FOCUS_IN, self.onFocusIn, tkext.TK_EVENT_BIND_ADD)
        self.getTk().bind(tkext.TK_EVENT_FOCUS_OUT, self.onFocusOut, tkext.TK_EVENT_BIND_ADD)

        self.getTk().bind(tkext.TK_EVENT_MOUSE_ENTER, self.onMouseEnter, tkext.TK_EVENT_BIND_ADD)
        self.getTk().bind(tkext.TK_EVENT_MOUSE_LEAVE, self.onMouseLeave, tkext.TK_EVENT_BIND_ADD)

    @property
    def IsFocusIn(self) -> bool:
        """ If the represented tkinter widget posses focus at the moment. """
        return self._focus

    @property
    def IsMouseEntered(self) -> bool:
        """ If the mouse cursor is currently hovering over the represented tkinter widget. """
        return self._mouseEntered

    def onMouseEnter(self, event):
        """ Called when the mouse pointer enters the represented widget. """
        self._mouseEntered = True

    def onMouseLeave(self, event):
        """ Called when the mouse pointer leaves the represented widget. """
        self._mouseEntered = False

    def onFocusIn(self, event):
        """ Called when the represented widget gains focus. """
        self._focus = True
    
    def onFocusOut(self, event):
        """ Called when the represented widget loses focus. """
        self._focus = False

class PanelCreationError(AppTkException):
    """ Exception related to errors during panel creations. """
    pass

class PaneledComponent(GraphicalComponent):
    """ Abstract graphical application component which may consist of dynamically created panels. See `Panel` for more information. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

    def createPanel(self, panelInterface: Type, tkMaster: tk.Widget = None, panelName: str = None):
        """ Creates and returns a panel for the given panel interface, tkinter parent and name.
        
        Parameters
        ----------
        panelInterface: `Type`
            The panel interface the panel has to implement.
        tkMaster: `tk.Widget` (default: `None`)
            The tkinter parent of the panel to create. If `None` the tkinter bond of this component is used.
        panelName: `str` (default: `None`)
            The name under which the panel has been registered. If `None` it is ignored.

        Returns
        -------
        panel: `Panel`
            The created panel if succeeded.
        """
        panelClass = self.getContext().Application.Manifest.getComponentClass(panelInterface, panelName)

        if panelClass is None or not issubclass(panelClass, Panel):
            raise PanelCreationError("Found '{}' for panel interface '{}' and name '{}' but it's not of required class '{}'."
                .format(panelClass, panelInterface, panelName, Panel))

        if tkMaster is None:
            tkMaster = self.getTk()
        elif tkMaster is not self.getTk() and tkMaster not in self.getTk().winfo_children():
            raise PanelCreationError("Can't create a panel whose tkinter master isn't part of its containing component tkinter widget.")

        return panelClass(tkMaster, self.getContext(), self.getComponentContext())

class Panel(PaneledComponent):
    """ Application component representing a composition of tkinter widgets which fulfill a specific purpose contained in a covering `tkinter.ttk.Frame`. 
    
    A Panel is a special application component which can only be created by a `PaneledComponent`. It is technically not part of its context but its component 
    which created it. It exists in the same context as its creator component and can be considered as an element the creator component consists of. Additionally
    it doesn't have its own component context but shares the same as its creator component. It is used to group tkinter widgets which fulfill a specific and 
    most likely general purpose which makes it reusable by other components. Panels have to be inserted like any other application component into the
    application's manifest.

    Note
    ----
    Inherit directly from this class to create a custom panel. The `__init__` signature shall never be changed.
    """
    def __init__(self, tkMaster, context: Context, componentContext: Context):
        super().__init__(tkMaster, context)

        self._componentContext = componentContext
    
    def getComponentContext(self) -> Context:
        return self._componentContext

    @property
    def MainFrame(self) -> ttk.Frame:
        """ The `tkinter.ttk.Frame` which covers the whole panel. Same as `self.getTk()`. """
        return self.getTk()

    def _createTkBond(self, tkMaster):
        return ttk.Frame(tkMaster)

class Window(PaneledComponent):
    """ Application component which represents a `tkinter.TopLevel` widget. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._componentContext = SubContext(self.getTk(), self.getContext())

        self.Window.protocol(tkext.TK_PROTOCOL_WINDOW_CLOSE_REQUEST, self.onWindowCloseClick)

    def getComponentContext(self) -> Context:
        return self._componentContext

    @property
    def Window(self) -> tk.Toplevel:
        """ Returns the `tkinter.TopLevel` widget the window belongs to, same as `self.getTk()`. """
        return self.getTk()

    @property
    def MenuBar(self) -> tk.Menu:
        """ Returns the `tk.Menu` which represents the window's respectively the `tkinter.TopLevel`'s menubar. """
        return self.Window.nametowidget(self.Window[tkext.TK_MENU_KEYWORD]) if self.Window[tkext.TK_MENU_KEYWORD] else None

    @MenuBar.setter
    def MenuBar(self, menuBar: tk.Menu):
        """ Sets the menubar of the window. """
        self.Window.configure(menu = menuBar)

    def createMenuBarIfNotExistent(self) -> tk.Menu:
        """ Returns the menubar of the window and creates it beforehand if it doesn't exist. """
        if self.MenuBar is None:
            self.MenuBar = tk.Menu(self.getTk())
        return self.MenuBar

    def setApplicationWindowIcon(self):
        """ Sets the window icon to the application's icon. """
        self.setWindowIcon(self.getContext().Application.IconFilePath)

    def setWindowIcon(self, iconPath: Path):
        """ Sets the icon of the window to the image the provided path points to. """
        self.Window.iconbitmap(iconPath.absolute().as_posix())

    def close(self):
        """ Destroy the associated `tkinter.TopLevel` widget and closes the window. """
        self.Window.destroy()

    def onWindowCloseClick(self):
        """ Called when the user clicks on the close/'x' button at the top right corner of the window."""
        self.close()

    def _createTkBond(self, tkMaster):
        return tk.Toplevel(tkMaster)

    def centerOnScreen(self):
        """ Centers the window in the middle of the screen. """
        tkext.centerWindowOnScreen(self.Window)

class Dialog(Window):
    """ A short term interaction window which yields a result.
    
    A Dialog represents a window which gains attention immedialtly after creation and blocks all other windows. It should serve a specific purpose 
    and be closed after it has served it. After a dialog has been closed it should have created an appropriate result object. If no result has been
    provided before the dialog has been closed the result will be `None`.  
    
    Note
    ----
    Inherit directly from this class to create custom dialogs. The `__init__` signature shall never be changed. Use `Dialog.waitForResult` to open
    a local tkinter event loop which will be sustained until the dialog has been destroyed. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)
        
        self._result = None
        self._resultWaitVariable = tk.BooleanVar(self.getTk(), False)

    @property
    def Result(self) -> Any:
        """ The result of the dialog. """
        return self._result

    @Result.setter
    def Result(self, result: Any):
        """ Sets the result of the dialog and notifies the local tkinter event loop that the result has been supplied. """
        self.onResultSet(result)
        self._resultWaitVariable.set(True)
        self._result = result

    @property
    def IsResultSet(self) -> bool:
        """ Returns if the result has been created/set. """
        return self._resultWaitVariable.get()

    def onCreate(self):
        self.centerOnScreen()
        
        self.Window.grab_set()
        self.Window.focus_set()

    def onFocusIn(self, event):
        self.Window.grab_set()

    def onDestroy(self, event):
        if not self.IsResultSet:
            self.Result = None

    def onResultSet(self, result):
        """ Called when the result is about to get set (not set yet). Note: This method might also be called during destruction of this dialog. """
        pass

    def waitForResult(self):
        """ Creates and enters a local tkinter event loop until the result of the dialog has been supplied (blocking but keeps the GUI alive). 
        Returns the dialog result afterwards. """
        while not self._resultWaitVariable.get():
            self.Window.wait_variable(self._resultWaitVariable)
        return self._result

class Applet(Window):
    """ A main window of an application. 
    
    An applet is an application component which represents a mostly independent window of the application, like a main window. Like any other application 
    component, an applet has to be registered in the application's manifest. An applet can be started by calling `Context.startApplet` in any context. The
    method `Applet.onStart` is called every time the applet has been started even if it has been created already and always before `Component.onCreate` gets
    called.   

    Note
    ----
    Inherit directly from this class to create custom applets. The `__init__` signature shall never be changed.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        if self.getContext().Application.Manifest.getProperties(self.__class__)[APPLET_PROPERTY_APPMENU]:
            menuBar = self.createMenuBarIfNotExistent()
            
            appMenu = tk.Menu(menuBar, tearoff = False)

            for componentClass, config in self.getContext().Application.Manifest.Applets:
                if config[APPLET_PROPERTY_ADD_TO_MENU]:
                    appMenu.add_command(label = config[APPLET_PROPERTY_MENU_ENTRY_NAME], command = lambda componentClass = componentClass: self._onAppMenuClick(componentClass))
            
            if isinstance(self.getContext(), ApplicationContext):
                appMenu.add_command(label = APPLET_MENU_ENTRY_QUIT, command = self.getContext().Application.quit)
            
            menuBar.add_cascade(label = APPLET_MENU_NAME, menu = appMenu)

    @showerror
    def _onAppMenuClick(self, appletClass: Type):
        self.getContext().startApplet(appletClass)
    
    def onStart(self, **startProperties):
        """ Called every time the applet has been started.
        
        Parameters
        ----------
        startProperties: `Dict` (default: `{}`)
            Any custom data which shall be passed to the applet. It has to be provided at `Context.startApplet`.
        """
        self.Window.focus_set()

class Service(Component):
    """ An interface to a specific functionality shared between all application components in the same context. 
    
    A service is an application component which implements a unified interface to a specific functionality and can be accessed in the context it is or 
    is going to be contained by calling `Context.requestService`. On every request the service should make sure that it is still able to serve its purpose. 
    A service is created as soon as it has been requested in any context. Every time the service has been requested the method `Service.onRequest` 
    is called even before `Component.onCreate` gets called. 
    
    Note
    ----
    Inherit directly from this class to create custom services. The `__init__` signature shall never be changed.
    """
    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._componentContext = SubContext(self.getTk(), context)

    def getComponentContext(self) -> Context:
        return self._componentContext

    def stop(self):
        """ Stops the service. """
        self.getTk().destroy()

    def onRequest(self, **requestProperties):
        """ Called every time the service has been requested. If the service can't serve its purpose anymore an exception should be raised. """
        pass

    def _createTkBond(self, tkMaster):
        toplevel = tk.Toplevel(tkMaster)
        toplevel.withdraw()
        return toplevel