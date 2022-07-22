""" 
Extension which adds a panel and dialog interface to create and configure serial connections as well as a default implementation, respectively. 

Interfaces
----------------
Panels: `SerialConfigurationPanel`
Dialogs: `SerialDialog`

Additional Derivables
----------------------
Dialogs: `VariabledSerialConfigurationPanel`

Implementations
---------------
Panels: `StandardSerialConfigurationPanel`
Dialogs: `StandardSerialDialog`
"""
from typing import Union

from dltscontrol.apptk import Panel, Dialog, showerror
from serial import serialutil, Serial, serial_for_url
from serial.tools import list_ports

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

# extension dependencies
from dltscontrol.app.core import OkAbortPanel, OkAbortDialog, PaneledOkAbortDialog

class SerialConfigurationPanel(Panel):
    """ Panel interface to configure and create a serial connection (`Serial`). """

    _PARITY_NAMES_REVERSED = {name: key for key, name in serialutil.PARITY_NAMES.items()}

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def getPort(self) -> str:
        raise NotImplementedError

    def setPort(self, port: str):
        raise NotImplementedError
    
    def getBaudrate(self) -> int:
        raise NotImplementedError

    def setBaudrate(self, baudrate: int):
        raise NotImplementedError

    def getBytesize(self) -> int:
        raise NotImplementedError

    def setBytesize(self, bytesize: int):
        raise NotImplementedError

    def getStopbits(self) -> float:
        raise NotImplementedError

    def setStopbits(self, stopbits: float):
        raise NotImplementedError

    def getParityName(self) -> str:
        raise NotImplementedError

    def setParityName(self, parity: str):
        raise NotImplementedError

    def getParityChar(self) -> str:
        return self._PARITY_NAMES_REVERSED[self.getParityName()]

    def setParityChar(self, parity: str):
        self.setParityName(serialutil.PARITY_NAMES[parity])

    def getTimeOut_ms(self) -> int:
        raise NotImplementedError

    def setTimeOut_ms(self, timeout_ms: int):
        raise NotImplementedError

    def createSerial(self) -> Serial:
        return serial_for_url(self.getPort(), self.getBaudrate(), self.getBytesize(), self.getParityChar(), self.getStopbits(), 
            self.getTimeOut_ms() / 1000 if self.getTimeOut_ms() is not None else None)

class VariabledSerialConfigurationPanel(SerialConfigurationPanel):
    """ Panel interface, variable based `SerialConfigurationPanel`. All configurable values are stored in tkinter variables. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._portVariable = tk.StringVar(self.getTk())
        self._baudrateVariable = tkext.IntNoneVar(self.getTk())
        self._byteSizeVariable = tkext.IntNoneVar(self.getTk())
        self._stopbitsVariable = tk.StringVar(self.getTk())
        self._parityNameVariable = tk.StringVar(self.getTk())
        self._timeOutMillisecondsVariable = tkext.IntNoneVar(self.getTk(), "")

    @property
    def PortVariable(self) -> tk.StringVar:
        return self._portVariable

    @property
    def BaudrateVariable(self) -> tkext.IntNoneVar:
        return self._baudrateVariable

    @property
    def ByteSizeVariable(self) -> tkext.IntNoneVar:
        return self._byteSizeVariable

    @property
    def StopbitsVariable(self) -> tk.StringVar:
        return self._stopbitsVariable

    @property
    def ParityNameVariable(self) -> tk.StringVar:
        return self._parityNameVariable

    @property
    def TimeOutMillisecondsVariable(self) -> tkext.IntNoneVar:
        return self._timeOutMillisecondsVariable

    def getPort(self) -> str:
        return self._portVariable.get()

    def setPort(self, port: str):
        return self._portVariable.set(port)
    
    def getBaudrate(self) -> int:
        return self._baudrateVariable.get()

    def setBaudrate(self, baudrate: int):
        self._baudrateVariable.set(baudrate)

    def getBytesize(self) -> int:
        return self._byteSizeVariable.get()

    def setBytesize(self, bytesize: int):
        self._byteSizeVariable.set(bytesize)

    def getStopbits(self) -> Union[int, float]:
        stopBits: str = self._stopbitsVariable.get()
        try:
            stopBits = int(stopBits)
        except:
            stopBits = float(stopBits)
        return stopBits

    def setStopbits(self, stopbits: Union[int, float]):
        self._stopbitsVariable.set(stopbits)

    def getParityName(self) -> str:
        return self._parityNameVariable.get()

    def setParityName(self, parity: str):
        self._parityNameVariable.set(parity)

    def getTimeOut_ms(self) -> int:
        return self._timeOutMillisecondsVariable.get()

    def setTimeOut_ms(self, timeout_ms: int):
        self._timeOutMillisecondsVariable.set(timeout_ms)

class StandardSerialConfigurationPanel(VariabledSerialConfigurationPanel):
    """ Panel which allows to create and configure a serial conncetion. """

    _ENTRY_WIDTH = 6

    _FRAME_PADX = 4
    _FRAME_PADY = 4

    # _FRAME_BORDER_WIDTH = 2
    # _FRAME_RELIEF = tkext.TK_RELIEF_RAISED

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        ports = tuple(map(lambda pi: pi.device, list_ports.comports()))
        baudrates = Serial.BAUDRATES
        bytesizes = Serial.BYTESIZES
        stopbits = Serial.STOPBITS
        parityNames = serialutil.PARITY_NAMES.values()

        portsFrame = ttk.Frame(self.MainFrame)
        portsLabel = ttk.Label(portsFrame, text = "Port:")
        self._portsOptionMenu = tkext.OptionMenu(portsFrame, self.PortVariable, next(iter(ports), None), *ports)
        self.PortVariable.set('COM5')       # TODO: DEBUG.. Remove me later

        baudFrame = ttk.Frame(self.MainFrame)
        baudLabel = ttk.Label(baudFrame, text = "Baudrate:")
        self._baudOptionMenu = tkext.OptionMenu(baudFrame, self.BaudrateVariable, next(iter(baudrates), None), *baudrates)

        byteSizeFrame = ttk.Frame(self.MainFrame)
        byteSizeLabel = ttk.Label(byteSizeFrame, text = "Bytesize:")
        self._bytesizeOptionMenu = tkext.OptionMenu(byteSizeFrame, self.ByteSizeVariable, next(iter(bytesizes), None), *bytesizes)

        stopBitsFrame = ttk.Frame(self.MainFrame)
        stopBitsLabel = ttk.Label(stopBitsFrame, text = "Stopbits:")
        self._stopbitsOptionMenu = tkext.OptionMenu(stopBitsFrame, self.StopbitsVariable, next(iter(stopbits), None), *stopbits)

        parityFrame = ttk.Frame(self.MainFrame)
        pariyLabel = ttk.Label(parityFrame, text = "Parity:")
        self._paritiesOptionMenu = tkext.OptionMenu(parityFrame, self.ParityNameVariable, next(iter(parityNames), None), *parityNames)

        timeOutFrame = ttk.Frame(self.MainFrame)
        timeOutLabel = ttk.Label(timeOutFrame, text = "Time Out [ms]:")
        timeOutEntry = tkext.IntEntry(timeOutFrame, textvariable = self.TimeOutMillisecondsVariable, width = self._ENTRY_WIDTH)

        portsLabel.pack(side = tk.LEFT); self._portsOptionMenu.pack(side = tk.LEFT)
        portsFrame.grid(row = 0, column = 0, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# portsFrame.pack(side = tk.LEFT, padx = 8)
        baudLabel.pack(side = tk.LEFT); self._baudOptionMenu.pack(side = tk.LEFT)
        baudFrame.grid(row = 0, column = 1, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# baudFrame.pack(side = tk.LEFT, padx = 8)
        byteSizeLabel.pack(side = tk.LEFT); self._bytesizeOptionMenu.pack(side = tk.LEFT)
        byteSizeFrame.grid(row = 1, column = 0, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# byteSizeFrame.pack(side = tk.LEFT, padx = 8)
        stopBitsLabel.pack(side = tk.LEFT, fill = tk.X); self._stopbitsOptionMenu.pack(side = tk.LEFT)
        stopBitsFrame.grid(row = 1, column = 1, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# stopBitsFrame.pack(side = tk.LEFT, padx = 8)
        pariyLabel.pack(side = tk.LEFT); self._paritiesOptionMenu.pack(side = tk.LEFT)
        parityFrame.grid(row = 1, column = 2, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# parityFrame.pack(side = tk.LEFT, padx = 8)
        timeOutLabel.pack(side = tk.LEFT); timeOutEntry.pack(side = tk.LEFT)
        timeOutFrame.grid(row = 0, column = 2, sticky = tk.W, padx = self._FRAME_PADX, pady = self._FRAME_PADY)# timeOutFrame.pack(side = tk.LEFT, padx = 8)

class SerialDialog(OkAbortDialog):
    """ Dialog interface to create a serial connection which is based on a `SerialConfigurationPanel`. The Result should be either `None` or of type `Serial`. """

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self._configPanel: SerialConfigurationPanel = self._createSerialConfigurationPanel()

    @property
    def SerialConfigurationPanel(self) -> SerialConfigurationPanel:
        """ The serial configuration panel of the dialog. """
        return self._configPanel

    @showerror
    def _onOk(self):
        self.Result = self._configPanel.createSerial()
        self.close()

    @showerror
    def _onAbort(self):
        self.close()

    def _createSerialConfigurationPanel(self) -> SerialConfigurationPanel:
        """ Creates and returns the serial configuration panel of the dialog. """
        raise NotImplementedError

class StandardSerialDialog(SerialDialog, PaneledOkAbortDialog):
    """ Dialog which allows to create and configure a serial connection. """

    _SERIAL_PANEL_BORDER_WIDTH = 2
    _SERIAL_PANEL_BORDER_RELIEF = tkext.TK_RELIEF_SUNKEN

    _SERIAL_PANEL_BORDER_PADX = 2

    _PANEL_PADY = 2

    def __init__(self, tkMaster, context):
        super().__init__(tkMaster, context)

        self.Window.title("Configure Serial Interface")
        self.Window.resizable(False, False)
        
        self.SerialConfigurationPanel.MainFrame.config(borderwidth = self._SERIAL_PANEL_BORDER_WIDTH, relief = self._SERIAL_PANEL_BORDER_RELIEF)

        self.SerialConfigurationPanel.getTk().pack(side = tk.TOP, padx = self._SERIAL_PANEL_BORDER_PADX)
        self.OkAbortPanel.getTk().pack(side = tk.TOP, pady = self._PANEL_PADY)

    def _createOkAbortPanel(self) -> OkAbortPanel:
        return self.createPanel(OkAbortPanel, self.Window)

    def _createSerialConfigurationPanel(self) -> SerialConfigurationPanel:
        return self.createPanel(SerialConfigurationPanel, self.Window)

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardSerialConfigurationPanel)

# dialogs
manifest.insert(StandardSerialDialog)