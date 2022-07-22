""" 
`tkinter` related classes, fields and extensions 
"""

from typing import List, Tuple, Callable, Union, Any

from dltscontrol.tools import PythonConstants

import sys
import math

import tkinter as tk
import tkinter.ttk as ttk

TK_EVENT_DESTROY = "<Destroy>"
TK_EVENT_FOCUS_IN = "<FocusIn>"
TK_EVENT_FOCUS_OUT = "<FocusOut>"

TK_EVENT_MOUSE_ENTER = "<Enter>"
TK_EVENT_MOUSE_LEAVE = "<Leave>"
TK_EVENT_MOUSE_WHEEL = "<MouseWheel>"

TK_EVENT_RETURN = "<Return>"
TK_EVENT_KEYPAD_ENTER = "<KP_Enter>"
TK_EVENT_ESCAPE = "<Escape>"

_TK_EVENT_MOUSE_BUTTON_PRESS_TEMPLATE = "<Button-{0}>"
_TK_EVENT_MOUSE_BUTTON_HELD_MOTION_TEMPLATE = "<B{0}-Motion>"
_TK_EVENT_MOUSE_BUTTON_RELEASE_TEMPLATE = "<ButtonRelease-{0}>"
_TK_EVENT_MOUSE_BUTTON_DOUBLE_TEMPLATE = "<Double-Button-{0}>"

TK_EVENT_BIND_ADD = "+"

TK_PROTOCOL_WINDOW_CLOSE_REQUEST = "WM_DELETE_WINDOW"
TK_PROTOCOL_FOCUS_TAKEN = "WM_TAKE_FOCUS"

TK_MENU_KEYWORD = "menu"
TK_CALLBACK_KEYWORD = "command"
TK_SELECTMODE_KEYWORD = "selectmode"

TK_TRACE_MODE_READ = "read"
TK_TRACE_MODE_WRITE = "write"
TK_TRACE_MODE_UNSET = "unset"

TK_RELIEF_FLAT = "flat"
TK_RELIEF_RAISED = "raised"
TK_RELIEF_SUNKEN = "sunken"
TK_RELIEF_GROOVE = "groove"
TK_RELIEF_RIDGE = "ridge"

TK_ORIENT_VERTICAL = "vertical"
TK_ORIENT_HORIZONTAL = "horizontal"

TK_VALIDATION_TRIGGER_KEY = "key"
TK_VALIDATION_TRIGGER_FOCUS = "focus"
TK_VALIDATION_TRIGGER_FOCUS_IN = "focusin"
TK_VALIDATION_TRIGGER_FOCUS_OUT = "focusout"
TK_VALIDATION_TRIGGER_ALL = "all"

TK_VALIDATION_ACTION_DELETE = 0
TK_VALIDATION_ACTION_INSERT = 1

TK_WIDGET_STATE_ACTIVE = "active"
TK_WIDGET_STATE_DISABLED = "disabled"
TK_WIDGET_STATE_FOCUS = "focus"
TK_WIDGET_STATE_PRESSED = "pressed"
TK_WIDGET_STATE_SELECTED = "selected"
TK_WIDGET_STATE_BACKGROUND = "background"
TK_WIDGET_STATE_READONLY = "readonly"
TK_WIDGET_STATE_ALTERNATE = "alternate"
TK_WIDGET_STATE_INVALID = "invalid"

TK_SCALE_IDENT_SLIDER_SUFFIX = "slider"
TK_SCALE_IDENT_TROUGH_SUFFIX = "trough"

TK_MOUSE_WHEEL_UP_BUTTON_NUMBER_LINUX = 4
TK_MOUSE_WHEEL_DOWN_BUTTON_NUMBER_LINUX = 5

TK_MOUSE_WHEEL_DELTA_ABS_WINDOWS = 120

def TK_EVENT_MOUSE_BUTTON_PRESS(number: int):
    return _TK_EVENT_MOUSE_BUTTON_PRESS_TEMPLATE.format(number)

def TK_EVENT_MOUSE_BUTTON_HELD_MOTION(number: int):
    return _TK_EVENT_MOUSE_BUTTON_HELD_MOTION_TEMPLATE.format(number)

def TK_EVENT_MOUSE_BUTTON_RELEASE(number: int):
    return _TK_EVENT_MOUSE_BUTTON_RELEASE_TEMPLATE.format(number)

def TK_EVENT_MOUSE_BUTTON_DOUBLE(number: int):
    return _TK_EVENT_MOUSE_BUTTON_DOUBLE_TEMPLATE.format(number)

def bindMouseWheel(widget: tk.Misc, func = None, add = None):
    """ Platform independent mouse wheel event bind. Adapts Linux events to Windows like events. Works at least on Windows and X11 systems. """
    if sys.platform.startswith(PythonConstants.PLATFORM_NAME_LINUX):
        def linuxEventDeltaAdapter(event, func = func):
            if event.num == TK_MOUSE_WHEEL_UP_BUTTON_NUMBER_LINUX:
                event.delta = TK_MOUSE_WHEEL_DELTA_ABS_WINDOWS
            elif event.num == TK_MOUSE_WHEEL_DOWN_BUTTON_NUMBER_LINUX:
                event.delta = -TK_MOUSE_WHEEL_DELTA_ABS_WINDOWS
            func(event)

        widget.bind(TK_EVENT_MOUSE_BUTTON_PRESS(TK_MOUSE_WHEEL_UP_BUTTON_NUMBER_LINUX), linuxEventDeltaAdapter, add)
        widget.bind(TK_EVENT_MOUSE_BUTTON_PRESS(TK_MOUSE_WHEEL_DOWN_BUTTON_NUMBER_LINUX), linuxEventDeltaAdapter, add)
    else:
        widget.bind(TK_EVENT_MOUSE_WHEEL, func, add)

def askSelection(tkMaster, *selectables, selectableCount = 1, converter: Callable[[Any], str] = lambda selectable: str(selectable), allowNone = True, title = "Select", bell = True) -> List:
    """ Opens a `SelectionDialog`, waits until it has been destroyed and returns the selected items. See `SelectionDialog`. """
    return SelectionDialog(tkMaster, *selectables, selectableCount = selectableCount, converter = converter, allowNone = allowNone, title = title, bell = True).show()

def centerWindowOnScreen(window: Union[tk.Tk, tk.Toplevel]):
        """ Centers the given window's position to the middle of the screen. """
        window.update_idletasks()

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))

        window.geometry("+{}+{}".format(int(screen_width / 2 - size[0] / 2), int(screen_height / 2 - size[1] / 2)))

class SelectionDialog(tk.Toplevel):
    """ Dialog which shows multiple selectable values. Selectables have to convertable to string by provided or the default converter. 
    
    Parameters
    ----------
    tkMaster:
        The tkinter parent of the dialog.
    selectables: `Sequence`:
        The selectable items which are going to shown for selection.
    selectableCount: `int` (default: `1`)
        The maximum of items which can be selected simultaniously
    converter: `Callable[[Any], str]` (default: `str(selectable)`)
        The function which converts a selectable into a `str`.
    allowNone: `bool` (default: `True`)
        Whether to allow an empty selection or not
    title: `str` (default: `"Select"`)
        The title of the dialog window.
    bell: `bool` (default: `True`)
        Whether to ring the bell if the intended selection by the user isn't possible or not.
    cnf: `Dict` (default: `{}`)
        The config for the `TopLevel` tkinter widget.
    kw: `Dict` (default: `{}`)
        The config for the `TopLevel` tkinter widget.
    """
    _DEFAULT_PAD = 2

    _BUTTON_WIDTH = 10

    def __init__(self, tkMaster, *selectables, selectableCount = 1, converter: Callable[[Any], str] = lambda selectable: str(selectable), 
        allowNone = True, title = "Select", bell = True, cnf = {}, **kw):
        
        self._allowNone = allowNone
        self._bell = bell
        self._selectableCount = selectableCount
        self._selectables = dict()
        self._selectableStrings = dict()
        self._selectableVariables = dict()

        for selectable in selectables:
            self._selectables[id(selectable)] = selectable
            self._selectableStrings[id(selectable)] = converter(selectable)
        
        super().__init__(tkMaster, cnf, **kw)
        
        # self.resizable(False, False)
        self.title(title) 
        self.geometry("300x125")

        selectionFrame = ttk.Frame(self)

        columns = int(len(self._selectables) ** 0.5)
        rows = math.ceil(len(self._selectables) / columns)

        for index, selectable in enumerate(self._selectables.values()):
            boolVar = tk.BooleanVar(self, index == 0 and not self._allowNone)
            self._selectableVariables[id(selectable)] = boolVar

            row = index % rows
            column = int(index / rows)

            radioButton = ttk.Checkbutton(selectionFrame, variable = boolVar, text = self._selectableStrings[id(selectable)], 
                command = lambda var = boolVar: self._onSelectionChange(var))
            radioButton.grid(row = row, column = column, sticky = tk.W, padx = self._DEFAULT_PAD, pady = self._DEFAULT_PAD)
        
        selectionFrame.pack(side = tk.TOP, fill = tk.BOTH, padx = self._DEFAULT_PAD, pady = self._DEFAULT_PAD)

        confirmationFrame = ttk.Frame(self)

        if self._allowNone:
            button = ttk.Button(confirmationFrame, text = "Cancel", width = self._BUTTON_WIDTH, command = self._onCancel)
            button.pack(side = tk.RIGHT, padx = self._DEFAULT_PAD, pady = self._DEFAULT_PAD)
        
        button = ttk.Button(confirmationFrame, text = "Ok", width = self._BUTTON_WIDTH, command = self._onConfirm)
        button.pack(side = tk.RIGHT, padx = self._DEFAULT_PAD, pady = self._DEFAULT_PAD)

        self.protocol(TK_PROTOCOL_WINDOW_CLOSE_REQUEST, self._onCancel)

        confirmationFrame.pack(side = tk.BOTTOM, fill = tk.X, padx = self._DEFAULT_PAD, pady = self._DEFAULT_PAD)
    
    def _onSelectionChange(self, variable: tk.BooleanVar):
        if len(self.get()) > self._selectableCount:
            variable.set(not variable.get())

            if self._bell:
                self.bell()

    def _onCancel(self):
        if not self._allowNone:
            if self._bell:
                self.bell()
        else:
            for variable in self._selectableVariables.values():
                variable.set(False)

            self.destroy()

    def _onConfirm(self):
        if not self.get() and not self._allowNone:
            if self._bell:
                self.bell()
        else:
            self.destroy()

    def show(self) -> List:
        """ Sets focus and grab to the dialog, waits until the dialog's window has been destroyed and returns the selected items. """
        centerWindowOnScreen(self)

        self.focus_set()
        self.grab_set()
        
        self.wait_window(self)

        return self.get()

    def get(self) -> List:
        """ Returns the currently selected items. """
        selection = list()

        for selectableId, variable in self._selectableVariables.items():
            if variable.get():
                selection.append(self._selectables[selectableId])
        
        return selection

class OptionMenu(ttk.OptionMenu):
    """ Option menu whose options can be changed easily, for everything else see `tkinter.ttk.OptionMenu`. """
    
    def __init__(self, master, variable, defaultValue = None, *values, **kwargs):
        super().__init__(master, variable, defaultValue, *values, **kwargs)

        self._variable = variable
        self._callback = kwargs.get(TK_CALLBACK_KEYWORD, None)
        self._values: Tuple = tuple(values)
    
    @property
    def Options(self) -> Tuple:
        """ The options of the option menu. """
        return self._values

    @Options.setter
    def Options(self, options: Tuple):
        self._values = options

        menu: tk.Menu = self[TK_MENU_KEYWORD]
        menu.delete(0, tk.END)

        for option in options:
            menu.add_command(label = option, command = tk._setit(self._variable, option, self._callback))

        if not self._variable.get() in options and options:
            self._variable.set(next(iter(options)))

    @property
    def Variable(self) -> tk.Variable:
        """ the selected option variable. """
        return self._variable

    # @property
    # def SelectedOption(self):
    #     return self._variable.get()

    # @SelectedOption.setter
    # def SelectedOption(self, option):
    #     if not option in self.Options:
    #         raise IndexError("Option {0} is not included in available options: {1}.".format(option, self.Options))
        
    #     self._variable.set(option)

class ValidationEntry(ttk.Entry):
    """ An `tkinter.ttk.Entry` which only allows input if it has been validated. 
    
    Parameters
    ----------
    master: 
        The tkinter master widget of this entry.
    allowEmtpy: `bool` (default: `True`)
        Whether to allow an empty entry or not. It is highly recommended to allow it since if the user mark the whole content of the entry
        and enters a new value the entry is first deleted and becomes empty before the new value is actually entered.
    bell: `bool` (default: `True`)
        Whether to ring a bill if the validation does not succeed or not. 
    """
    def __init__(self, master, allowEmtpy = True, bell = True, **kw):
        super().__init__(master, **kw)
        
        self._allowEmpty = allowEmtpy
        self._ringBell = bell

        self.configure(validate = TK_VALIDATION_TRIGGER_KEY, validatecommand = (self.register(self._onKeyPressValidate), "%d", "%P", "%S"))

    def _onKeyPressValidate(self, action: int, entryValueIfAllowed: str, insertDeletedValue: str) -> bool:
        validationResult = self._validateEntryModification(action, entryValueIfAllowed, insertDeletedValue)
        
        if not entryValueIfAllowed:
            validationResult = self._allowEmpty

        if not validationResult and self._ringBell:
            self.bell()

        return validationResult

    def _validateEntryModification(self, action: int, entryValueIfAllowed: str, insertDeletedValue: str) -> bool:
        """ Validates the modifications of the entry on every keystroke. 
        
        Parameters
        ----------
        action: `int`
            The action performed on the entry, see `TK_VALIDATION_ACTION_INSERT` and `TK_VALIDATION_ACTION_DELETE`.
        entryValueIfAllowed: `str`
            The new value of the entry if the validation succeeds, this method returns `True` respectively.
        insertDeletedValue: `str`
            The value that is about to get inserted/appended to the entry's value.

        Returns
        -------
        validationResult: `bool`
            `True` if the entry modification shall be processed, otherwise `False`.
        """
        raise NotImplementedError

class NumberEntry(ValidationEntry):
    """ An `tkinter.ttk.Entry` which is meant to validate entries which only allow number types like `int` or `float`. See: `ValidationEntry`. 
    
    Paramters
    ---------
    allowNegatives: `bool` (default: `False`)
        Whether to allow negative values to be inserted or not.
    minValue: `Any` (default: `None`)
        The minimum value to be allowed. If no negative values are allowed a negative min value has no effect. If `None` no lower boundary is set.
    maxValue: `Any` (default: `None`)
        The maximum value to be allowed. If `None` no upper boundary is set.
    """
    _LEADING_CHAR_NEGATIVE_NUMBER = "-"

    def __init__(self, master, allowEmtpy = True, bell = True, allowNegatives = False, minValue = None, maxValue = None, **kw):
        super().__init__(master, allowEmtpy, bell, **kw)

        self._allowNegatives = allowNegatives
        self._minValue = minValue
        self._maxValue = maxValue

    @property
    def AllowNegatives(self) -> bool:
        return self._allowNegatives

    @AllowNegatives.setter
    def AllowNegatives(self, allowNegatives: bool):
        self._allowNegatives = allowNegatives

    @property
    def MinValue(self):
        return self._minValue

    @MinValue.setter
    def MinValue(self, minValue):
        self._minValue = minValue

    @property
    def MaxValue(self):
        return self._maxValue

    @MaxValue.setter
    def MaxValue(self, maxValue):
        self._maxValue = maxValue

    def _entryStringValueToNumber(self, entryValue: str):
        """ Converts the given entry string value to a number. May throw an exception if it fails. """
        raise NotImplementedError

    def _validateEntryModification(self, action, entryValueIfAllowed, insertDeletedValue):
        validValue = False

        try:
            if self._allowNegatives and entryValueIfAllowed == self._LEADING_CHAR_NEGATIVE_NUMBER:
                validValue = True
            else:
                value = self._entryStringValueToNumber(entryValueIfAllowed)

                validValue = (value >= 0 or self._allowNegatives) and (self._minValue is None or value >= self._minValue) and \
                    (self._maxValue is None or value <= self._maxValue) 
        except:
            pass

        return validValue

class IntEntry(NumberEntry):
    """ An `tkinter.ttk.Entry` which only allows values which are parseable to `int` values. """

    def __init__(self, master, allowEmtpy = True, bell = True, allowNegatives = False, minValue: int = None, maxValue: int = None, **kw):
        super().__init__(master, allowEmtpy, bell, allowNegatives, minValue, maxValue, **kw)

    def _entryStringValueToNumber(self, entryValue):
        return int(entryValue)

class FloatEntry(NumberEntry):
    """ An `tkinter.ttk.Entry` which only allows values which are parseable to `float` values. """

    def __init__(self, master, allowEmtpy = True, bell = True, allowNegatives = False, minValue: float = None, maxValue: float = None, **kw):
        super().__init__(master, allowEmtpy, bell, allowNegatives, minValue, maxValue, **kw)

    def _entryStringValueToNumber(self, entryValue):
        return float(entryValue)

class CustomValidationEntry(ValidationEntry):
    """ A `ValidationEntry` which only allows modifications if the provided predicate validates to `True`. See `ValidationEntry`. 
    
    Parameters
    ----------
    validationPredicate: `Callable[[int, str, str], bool]`
        The predicate which is called on entry value validation. See `ValidationEntry._validateEntryModification`.
    """
    def __init__(self, master, validationPredicate: Callable[[int, str, str], bool], allowEmtpy = True, bell = True, **kw):
        super().__init__(master, allowEmtpy, bell, **kw)

        self._validationPredicate = validationPredicate

    def _validateEntryModification(self, action: int, entryValueIfAllowed: str, insertDeletedValue: str) -> bool:
        return self._validationPredicate(action, entryValueIfAllowed, insertDeletedValue)

class IntNoneVar(tk.Variable):
    """ Value holder for integer variables which returns `None` on an empty variable/string. """

    _default = 0

    def __init__(self, master=None, value=None, name=None):
        """Construct an integer variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        super().__init__(master, value, name)

    def set(self, value):
        """Set the variable to VALUE."""

        if not isinstance(value, int):
            try:
                value = int(value)
            except:
                value = ""

        return super().set(value)

    def get(self):
        """Return the value of the variable as an integer or `NoneType`."""
        value = super().get()

        if not isinstance(value, int):
            try:
                value = int(value)
            except:
                value = None

        return value

class DoubleNoneVar(tk.Variable):
    """Value holder for float variables which returns `None` on an empty variable/string."""

    _default = 0.0

    def __init__(self, master=None, value=None, name=None):
        """Construct a float variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0.0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        super().__init__(master, value, name)

    def set(self, value):
        """Set the variable to VALUE."""

        if not isinstance(value, float):
            try:
                value = float(value)
            except:
                value = ""

        return super().set(value)

    def get(self):
        """Return the value of the variable as a float or `NoneType`."""
        value: str = super().get()

        if not isinstance(value, float):
            try:
                value = float(value)
            except:
                value = None

        return value

class DragDropListbox(tk.Listbox):
    """ A `tkinter.listbox` with drag'n'drop reordering of entries. """

    def __init__(self, master, **kw):
        # kw[TK_SELECTMODE_KEYWORD] = tk.SINGLE
        super().__init__(master, kw)

        self.bind(TK_EVENT_MOUSE_BUTTON_PRESS(1), self._onItemSelect)
        self.bind(TK_EVENT_MOUSE_BUTTON_HELD_MOTION(1), self._onItemMove)

        self.curIndex = None

    def _onItemSelect(self, event):
        self.curIndex = self.nearest(event.y)

    def _onItemMove(self, event):
        if len(self.curselection()) <= 1:
            i = self.nearest(event.y)
            if i < self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i+1, x)
                self.curIndex = i
            elif i > self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i-1, x)
                self.curIndex = i

class PeriodicCaller:
    """ Keeps calling a provided function in certain period of time using `tkinter.Misc.after` of any `tkinter.Misc` object. 
    
    Paramters
    ---------
    tkMaster: `Misc`
        The misc object which holds the tkinter task.
    period_ms: `int`
        The period of the function calling task.
    function: `Callable`
        The function to call. If it returns something which is interpreted as `True` in an `if` statement the periodic calling stops.
    *functionArgs:
        The arguments to be passed to the function to call.
    **functionKwArgs:
        The keyword arguments to be passed to the function to call.
    """
    def __init__(self, tkMaster: tk.Misc, period_ms: int, function: Callable, *functionArgs, **functionKwArgs):
        self._tkMaster = tkMaster
        self._period_ms = period_ms
        self._function = function
        self._functionArgs = functionArgs
        self._functionKwArgs = functionKwArgs

        self._taskId = None

    @property
    def IsRunning(self):
        """ If the calling task is still running. """
        return self._taskId is not None

    def start(self, callImmediately = True):
        """ Start the calling task. 
        
        Parameters
        ----------
        callImmediately: `bool` (default: `True`)
            Whether to call the function to call immediately or start calling it after the first period has passed.
        """
        if self._taskId is None:
            self._run(callImmediately)

    def _run(self, callImmediately = True):
        if not callImmediately or not self._function(*self._functionArgs, **self._functionKwArgs):
            self._taskId = self._tkMaster.after(self._period_ms, self._run)

    def cancel(self):
        """ Stops the calling task. """
        if self._taskId is not None:
            self._tkMaster.after_cancel(self._taskId)
            self._taskId = None