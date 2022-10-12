"""
Module to control and communicate with DTLSs.

This module provides an API to communicate with and acquire data from DLTSs. It relys on a custom `DltsConnection` implementation. Once the
DLTS connection has been implemented it can be used to command the connected DLTS. Furthermore a `DLTS` may be used to get an even more
abstract and convenient communication interface to the DLTS.

Example
-------
>>> MyDltsConnection(DltsConnection):
>>>     pass # implement it
>>> dlts = Dlts(MyDltsConnection())
>>> dlts.getX()
>>> # ...
"""

from typing import Tuple, List, Callable, TypeVar, Generic, Sequence, Type, Union, Iterable
from collections import deque
from io import RawIOBase


from dltscontrol import event

import logging
import numpy as np
import enum
import math
import time
import datetime
import threading
import pickle
import skimage.transform as skitrans
#
from dltscontrol.color_print import cprint

logger = logging.getLogger(__name__)

class DltsException(Exception):
    """ Base exception class for this module """
    pass

class DltsConstants:
    """ DLTS related constants. """

    DLTS_STRING_ENCODING = "ascii"
    DLTS_INT_BYTE_ORDER = "big"

    DLTS_COMMAND_HEADER_LENGTH = 3
    DLTS_RESPONSE_HEADER_LENGTH = 3

    DLTS_AUTOFOCUS_RESPONSE_LENGTH = 10  # NEW

    DLTS_RESPONSE_ACKNOWLEDGE = "ack"
    DLTS_RESPONSE_ERROR = "err"
    DLTS_RESPONSE_DATA = "dat"

    DLTS_LINE_TERMINATOR = "\r\n"

class DltsCommand:
    """ Implementation of all commands of the DLTS Protocol version 190425. """

    #command types
    _SET = "s"
    _GET = "g"
    _ACTION = "a"

    #command subjects
    _POSITION = "p"
    _STEPSIZE = "s"
    _DELAY = "d"
    _BOUNDARY_LOW = "l"
    _BOUNDARY_HIGH = "h"

    _LASER = "l"
    _SCAN = "s"
    _AUTOMATIC = "a"

    #subject parameters
    _X_AXIS = "x"
    _Y_AXIS = "y"
    _Z_AXIS = "z"
    _TILT_AXIS = "t"

    _I_AXIS = "i"

    _INTENSITY = "i"
    _MIN_INTENSITY = "e"
    _MAX_INTENSITY = "g"
    _PULSE_INTENSITY = "p"
    _PULSE_FREQUENCY = "f"

    _LATCH_UP_TURN_OFF_DELAY_MICRO = "u"
    _LATCH_UP_TURN_OFF_DELAY_MILLI = "m"

    _PIXEL = "p"
    _POINT = "p"
    _LINE = "l"
    _AREA = "a"
    _LATCHUP = "u"
    _MULTISCAN = "n"
    _AUTOFOCUS = "J"


    _STOP = "s"

    _PULSE = "p"
    _FOCUS = "f"

    @staticmethod
    def _encode(command: str) -> bytes:
        return command.encode(DltsConstants.DLTS_STRING_ENCODING)

    @staticmethod
    def _encodeToUInt16(value: int) -> bytes:
        encoded: bytes = None

        try:
            encoded = value.to_bytes(2, DltsConstants.DLTS_INT_BYTE_ORDER)
        except OverflowError as oe:
            raise DltsException("Can't convert {0} to UInt16.".format(value)) from oe

        return encoded

    # set commands

    @staticmethod
    def SetUInt16(setSubject: str, value: int) -> bytes:
        return DltsCommand._encode("{0}{1}".format(DltsCommand._SET, setSubject)) + DltsCommand._encodeToUInt16(value)

    @staticmethod
    def SetPosition(axis: str, position: int) -> bytes:
        return DltsCommand.SetUInt16("{0}{1}".format(DltsCommand._POSITION, axis), position)

    @staticmethod
    def SetXPosition(position: int) -> bytes:
        return DltsCommand.SetPosition(DltsCommand._X_AXIS, position)

    @staticmethod
    def SetYPosition(position: int) -> bytes:
        return DltsCommand.SetPosition(DltsCommand._Y_AXIS, position)

    @staticmethod
    def SetZPosition(position: int) -> bytes:
        return DltsCommand.SetPosition(DltsCommand._Z_AXIS, position)

    @staticmethod
    def SetXTilt(position: int) -> bytes:
        return DltsCommand.SetPosition(DltsCommand._TILT_AXIS, position)

    @staticmethod
    def SetScanAxisBoundary(axis: str, boundaryEnd: str, boundary: int) -> bytes:
        return DltsCommand.SetUInt16("{0}{1}".format(axis, boundaryEnd), boundary)

    @staticmethod
    def SetScanAxisHighBoundary(axis: str, boundary: int) -> bytes:
        return DltsCommand.SetScanAxisBoundary(axis, DltsCommand._BOUNDARY_HIGH, boundary)

    @staticmethod
    def SetScanAxisLowBoundary(axis: str, boundary: int) -> bytes:
        return DltsCommand.SetScanAxisBoundary(axis, DltsCommand._BOUNDARY_LOW, boundary)

    @staticmethod
    def SetScanXAxisLowBoundary(boundary: int) -> bytes:
        return DltsCommand.SetScanAxisLowBoundary(DltsCommand._X_AXIS, boundary)

    @staticmethod
    def SetScanXAxisHighBoundary(boundary: int) -> bytes:
        return DltsCommand.SetScanAxisHighBoundary(DltsCommand._X_AXIS, boundary)

    @staticmethod
    def SetScanYAxisLowBoundary(boundary: int) -> bytes:
        return DltsCommand.SetScanAxisLowBoundary(DltsCommand._Y_AXIS, boundary)

    @staticmethod
    def SetScanYAxisHighBoundary(boundary: int) -> bytes:
        return DltsCommand.SetScanAxisHighBoundary(DltsCommand._Y_AXIS, boundary)

    @staticmethod
    def SetScanAxisStepSize(axis: str, stepsize: int) -> bytes:
        return DltsCommand.SetUInt16("{0}{1}".format(DltsCommand._STEPSIZE, axis), stepsize)

    @staticmethod
    def SetScanXStepSize(stepsize: int) -> bytes:
        return DltsCommand.SetScanAxisStepSize(DltsCommand._X_AXIS, stepsize)

    @staticmethod
    def SetScanYStepSize(stepsize: int) -> bytes:
        return DltsCommand.SetScanAxisStepSize(DltsCommand._Y_AXIS, stepsize)

    @staticmethod
    def SetDelay(delayParameter: str, delay: int) -> bytes:
        return DltsCommand.SetUInt16("{0}{1}".format(DltsCommand._DELAY, delayParameter), delay)

    @staticmethod
    def SetScanPixelDelay(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._PIXEL, delay)

    @staticmethod
    def SetScanXDelay(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._PIXEL, delay)

    @staticmethod
    def SetScanLineDelay(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._LINE, delay)

    @staticmethod
    def SetScanYDelay(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._LINE, delay)

    @staticmethod
    def SetLatchUpTurnOffDelayMicroseconds(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._LATCH_UP_TURN_OFF_DELAY_MICRO, delay)

    @staticmethod
    def SetLatchUpTurnOffDelayMilliseconds(delay: int) -> bytes:
        return DltsCommand.SetDelay(DltsCommand._LATCH_UP_TURN_OFF_DELAY_MILLI, delay)

    @staticmethod
    def SetLaserParameter(laserParameter: str, value: int) -> bytes:
        return DltsCommand.SetUInt16("{0}{1}".format(DltsCommand._LASER, laserParameter) , value)

    @staticmethod
    def SetLaserIntensity(intensity: int) -> bytes:
        return DltsCommand.SetLaserParameter(DltsCommand._INTENSITY, intensity)

    @staticmethod
    def SetLaserPulseIntensity(intensity: int) -> bytes:
        return DltsCommand.SetLaserParameter(DltsCommand._PULSE_INTENSITY, intensity)

    @staticmethod
    def SetLaserPulseFrequency(frequency: int) -> bytes:
        return DltsCommand.SetLaserParameter(DltsCommand._PULSE_FREQUENCY, frequency)

    @staticmethod  # NEW
    def SetLaserMinIntensity(value: int) -> bytes:
        return DltsCommand.SetLaserParameter(DltsCommand._MIN_INTENSITY, value)  # NEW

    @staticmethod  # NEW
    def SetLaserMaxIntensity(value: int) -> bytes:
        return DltsCommand.SetLaserParameter(DltsCommand._MAX_INTENSITY, value)  # NEW

    @staticmethod  # NEW
    def SetLaserIntensityStep(value: int) -> bytes:
        return DltsCommand.SetScanAxisStepSize(DltsCommand._I_AXIS, value)  # NEW

    # get commands

    @staticmethod
    def GetUInt16(getSubject: str) -> bytes:
        return DltsCommand._encode("{0}{1}".format(DltsCommand._GET, getSubject))

    @staticmethod
    def GetPosition(axis: str) -> bytes:
        return DltsCommand.GetUInt16("{0}{1}".format(DltsCommand._POSITION, axis))

    @staticmethod
    def GetXPosition() -> bytes:
        return DltsCommand.GetPosition(DltsCommand._X_AXIS)

    @staticmethod
    def GetYPosition() -> bytes:
        return DltsCommand.GetPosition(DltsCommand._Y_AXIS)

    @staticmethod
    def GetZPosition() -> bytes:
        return DltsCommand.GetPosition(DltsCommand._Z_AXIS)

    @staticmethod
    def GetXTilt() -> bytes:
        return DltsCommand.GetPosition(DltsCommand._TILT_AXIS)

    @staticmethod
    def GetLaserParameter(laserParameter: str) -> bytes:
        return DltsCommand.GetUInt16("{0}{1}".format(DltsCommand._LASER, laserParameter))

    @staticmethod
    def GetLaserIntensity() -> bytes:
        return DltsCommand.GetLaserParameter(DltsCommand._INTENSITY)

    @staticmethod
    def GetLaserPulseIntensity() -> bytes:
        return DltsCommand.GetLaserParameter(DltsCommand._PULSE_INTENSITY)

    @staticmethod
    def GetLaserPulseFrequency() -> bytes:
        return DltsCommand.GetLaserParameter(DltsCommand._PULSE_FREQUENCY)

    # action commands

    @staticmethod
    def Action(actionSubject: str) -> bytes:
        return DltsCommand._encode("{0}{1}".format(DltsCommand._ACTION, actionSubject))

    @staticmethod
    def ActionAutomatic(automaticParamter: str) -> bytes:
        return DltsCommand.Action("{0}{1}".format(DltsCommand._AUTOMATIC, automaticParamter))

    @staticmethod
    def ActionAutoFocus() -> bytes:
        return DltsCommand.ActionAutomatic(DltsCommand._FOCUS)

    @staticmethod
    def ActionScan(scanParameter: str) -> bytes:
        return DltsCommand.Action("{0}{1}".format(DltsCommand._SCAN, scanParameter))

    @staticmethod
    def ActionScanAutoFocus() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._AUTOFOCUS)

    @staticmethod
    def ActionScanPoint() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._POINT)

    @staticmethod
    def ActionScanLine() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._LINE)

    @staticmethod
    def ActionScanArea() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._AREA)

    @staticmethod
    def ActionScanLatchup() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._LATCHUP)

    @staticmethod
    def ActionScanMultiScan() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._MULTISCAN)

    @staticmethod
    def ActionScanStop() -> bytes:
        return DltsCommand.ActionScan(DltsCommand._STOP)

    @staticmethod
    def ActionLaser(laserParameter: str) -> bytes:
        return DltsCommand.Action("{0}{1}".format(DltsCommand._LASER, laserParameter))

    @staticmethod
    def ActionLaserPulse() -> bytes:
        return DltsCommand.ActionLaser(DltsCommand._PULSE)

class DltsTimeoutError(DltsException):
    """ DLTS timed out. """
    pass

class DltsConnectionAcquisitionError(DltsException):
    """ DLTS is in use by someone else. Acquisition failed. """
    pass

class DltsProtocolError(DltsException):
    """ DLTS protocol has been violated. """
    pass

class DltsFirmwareError(DltsException):
    """ DLTS firmware notified an error. """
    pass

class DltsConnection:
    """ Thread safe implementation of the DLTS-Protocol. Implementations have to provides a basic binary communication interface. """

    def __init__(self):
        self._comLock = threading.RLock()
        self._acquired = False

    @property
    def IsAcquired(self):
        """ Returns if the DLTS connection has been acquired by any thread. """
        return self._acquired

    @property
    def IsAcquiredByMe(self):
        """ Returns if the DLTS Connection has been acquired by the calling thread. """
        acquired = self._comLock.acquire(False)

        if acquired:
            acquired = self._acquired
            self._comLock.release()

        return acquired

    def _acquireForTemporaryUsage(self):
        """ Acquires the DLTS connection on a temporary base and raises an exception if it doesn't succeed. """
        if not self._comLock.acquire(False):
            raise DltsConnectionAcquisitionError("Can't acquire the DLTS Connection since it has already been acquired.")

    def _releaseFromTemporaryUsage(self):
        """ Releases the DLTS connection from temporary usage. """
        self._comLock.release()

    def acquire(self, blocking: bool = False, timeout: float = -1):
        """ Acquires the DLTS connection by the calling thread. Multiple calls have no effect if already acquired. """
        acquired = self._comLock.acquire(blocking, timeout)

        if acquired:
            if self._acquired:
                self._comLock.release()
            else:
                self._acquired = True

        return acquired

    def release(self):
        """ Releases the DLTS connection. """
        if self.IsAcquiredByMe:
            self._acquired = False

        self._comLock.release()

    def __enter__(self):
        """ Acquire the DLTS connection. """
        if not self.IsAcquiredByMe:
            self.acquire(True)
        return self

    def __exit__(self, type, value, traceback):
        """ Release the DLTS connection. """
        self.release()

    @property
    def IsOpen(self) -> bool:
        """ Returns if the DLTS is connected. """
        return self._IsOpenUnlocked

    def close(self):
        """ Closes the DLTS connection. """
        self._closeUnlocked()

    def write(self, data: bytes) -> int:
        """ Sends the given data to the connected DLTS. Acquires the DLTS connection. """
        self._acquireForTemporaryUsage()

        try:
            return self._writeUnlocked(data)
        finally:
            self._releaseFromTemporaryUsage()

    def read(self, size = 1, force = True) -> bytes:
        """ Reads the specified amount of data sent from the connected DLTS and returns it. Acquires the DLTS connection. If forced raises an exception on timeout.  """
        self._acquireForTemporaryUsage()

        try:
            received = self._readUnlocked(size)

            if force and len(received) < size:
                raise DltsTimeoutError("Forced read expected {} bytes but received only {}".format(size, len(received)))

            return received
        finally:
            self._releaseFromTemporaryUsage()

    def readUntil(self, terminator: bytes = b"\n", size: int = None, force = True) -> bytes:
        """ Reads data sent from the connected DLTS until the given termination sequence occurs or the given size has been reached and returns it. If forced raises an exception on timeout.

        Warning
        -------
        If the underlying implementation has no timeout configured this method may block forever.
        """
        self._acquireForTemporaryUsage()

        try:
            received = bytearray()

            while not received.endswith(terminator) and (size is None or size < len(received)):
                receivedByte = self._readUnlocked(1)

                if force and not len(receivedByte):
                    raise DltsTimeoutError("Forced read until ran into timeout before terminator of maximum size had been reached.")

                received.append(int.from_bytes(receivedByte, DltsConstants.DLTS_INT_BYTE_ORDER))

            return bytes(received)
        finally:
            self._releaseFromTemporaryUsage()

    def readAll(self) -> bytes:
        """ Reads all available data sent from the connected DLTS.

        Warning
        -------
        If the underlying implementation has no timeout configured this method may block forever. """
        self._acquireForTemporaryUsage()

        try:
            return self._readAllUnlocked()
        finally:
            self._releaseFromTemporaryUsage()

    def command(self, command: bytes, expectedResponseHeader: str = DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE, responseDataSize = 0) -> bytes:
        """ Sends the given command to the connected DLTS and awaits the specified response. Reads additional data afterwards and returns it if specified. """
        self._acquireForTemporaryUsage()
        print ( command )	#for debugging serial communication

        try:
            data = None



            self.write(command)

            header = self.read(DltsConstants.DLTS_RESPONSE_HEADER_LENGTH).decode(DltsConstants.DLTS_STRING_ENCODING)

            if header != expectedResponseHeader:
                try:
                    commandString = command[:DltsConstants.DLTS_COMMAND_HEADER_LENGTH].decode(DltsConstants.DLTS_STRING_ENCODING)

                    if header == DltsConstants.DLTS_RESPONSE_ERROR:
                        error = self.readUntil(DltsConstants.DLTS_LINE_TERMINATOR)
                        raise DltsFirmwareError("Dlts responded with error '{}' to command '{}'.".format(error, commandString))
                    else:
                        # unknown response, clear input buffer to avoid further unexpected behaviour
                        self.readAll()

                        raise DltsProtocolError("Dlts responded with '{}' to command '{}' but '{}' was expected."
                            .format(header, commandString, expectedResponseHeader))
                except Exception as e:
                    cprint(f' DATA UNREAD = {command[:DltsConstants.DLTS_COMMAND_HEADER_LENGTH]}', 'debug_r')
            elif responseDataSize:
                data = self.read(responseDataSize)

            cprint(f'    {header} - {data} = {int.from_bytes(data, "big")if data is not None else None}')# TODO: DEBUG.. Remove me later

            return data
        finally:
            self._releaseFromTemporaryUsage()

    def commandSkipUntilResponse(self, command: bytes, expectedResponseHeader: str = DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE):
        """ Sends the given command to the connected DLTS and skips all incoming data until the specified response has been received. """
        self._acquireForTemporaryUsage()

        try:
            self.write(command)
            self.readUntil(expectedResponseHeader.encode(DltsConstants.DLTS_STRING_ENCODING))
        finally:
            self._releaseFromTemporaryUsage()

    def commandSet(self, command: bytes):
        """ Sends a SET command to the connected DLTS. """
        self.commandWithAcknowledge(command)

    def commandGet(self, command: bytes, dataSize: int) -> bytes:
        """ Sends a GET command to the connected DLTS and returns the received byte data of the specified amount. """
        return self.commandDataRetrieval(command, dataSize)

    def commandGetUInt(self, command: bytes, bytesCount: int) -> int:
        """ Sends a GET command to the connected DLTS and expects an unsigned integer in return of the specified length. Returns the received unsigned integer. """
        return int.from_bytes(self.commandGet(command, bytesCount), DltsConstants.DLTS_INT_BYTE_ORDER)

    def commandGetUInt8(self, command: bytes) -> int:
        """ Sends a GET command to the connected DLTS and expects an one byte long unsigned integer in return. Returns the received unsigned integer. """
        return self.commandGetUInt(command, 1)

    def commandGetUInt16(self, command: bytes) -> int:
        """ Sends a GET command to the connected DLTS and expects a two byte long unsigned integer in return. Returns the received unsigned integer. """
        return self.commandGetUInt(command, 2)

    def commandWithAcknowledge(self, command: bytes):
        """ Sends a command to the connected DLTS which is expected to get acknowledged. """
        self.command(command, DltsConstants.DLTS_RESPONSE_ACKNOWLEDGE, 0)

    def commandScanStart(self, command: bytes):
        """ Sends a scan start command to the connected DLTS. """
        self.command(command, DltsConstants.DLTS_RESPONSE_DATA, 0)

    def commandDataRetrieval(self, command: bytes, dataSize: int) -> bytes:
        """ Sends a command to the connected DLTS which is expected to be responded with byte data of the specified length. Returns the received data. """
        return self.command(command, DltsConstants.DLTS_RESPONSE_DATA, dataSize)


    # corresponding non thread-safe methods to be implemented by subclasses.
    @property
    def _IsOpenUnlocked(self) -> bool:
        raise NotImplementedError

    def _closeUnlocked(self):
        raise NotImplementedError

    def _writeUnlocked(self, data: bytes) -> int:
        raise NotImplementedError

    def _readUnlocked(self, size = 1) -> bytes:
        raise NotImplementedError

    def _readAllUnlocked(self) -> bytes:
        raise NotImplementedError

class ScanDataException(DltsException):
    """ Base exception for all failures during scan data processing. """
    pass

class IScanDataPoint:
    """ Base interface for all scan data points. Provides access to the scanned raw data. """

    @property
    def RawData(self) -> bytes:
        """ Returns the scanned raw data as bytes. """
        raise NotImplementedError

class ScanDataPoint(IScanDataPoint):
    """ Abstract base class for all scan data points. Consists of the scanned raw data to be interpreted by subclasses."""

    def __init__(self, rawData: bytes):
        self._rawData = rawData

    @property
    def RawData(self):
        return self._rawData

class INamed:
    """ Any object which should posses a name. Mostly for displaying purposes. """

    def getName(self) -> str:
        """ Optional name which describes this instance. """
        return self.__class__.__name__

class IScanImage(INamed):
    """ Data image which contains native scan data in a `numpy.ndarray`. """

    def getResolution(self) -> Tuple[int, int]:
        """ Returns the resolution of the stored data image. first value -> # of columns (2nd image dimension), second value -> # of rows (1st image dimension) """
        raise NotImplementedError

    def getSize(self) -> Tuple[int, int]:
        """ Returns the occupied real world space of the stored data image. first value -> space in row direction (2nd image dimension),
        second value -> space in column direction (1st image dimension) """
        raise NotImplementedError

    def getPosition(self) -> Tuple[int, int]:
        """ Returns the position from where the stored data image starts spanning. (top-left corner) first value -> start point in row direction (2nd image dimension),
        second value -> start point in column direction (1st image dimension) """
        raise NotImplementedError

    def getDataPointSize(self) -> Tuple[int, int]:
        """ Returns the occupied real world space of each data point/pixel of the data image. first value -> occupied space in row direction (2nd image dimension),
        second value -> occupied space in column direction (1st image dimension)"""
        return (int(self.getSize()[0] / self.getResolution()[0]), int(self.getSize()[1] / self.getResolution()[1]))

    def getImageArray(self) -> np.ndarray:
        """ Returns the scan data as `numpy.ndarray`. May have more than 2 dimensions. Size of first 2 dimensions is equal to the reversed image resolution. """
        raise NotImplementedError

    def getLaserIntensity(self) -> int:
        """ Returns the laser intensity the image was made with. """
        raise NotImplementedError

    def getZPosition(self) -> int:
        """ Returns the z/focus position the image was made with. """
        raise NotImplementedError

    def getXTilt(self) -> int:
        """ Returns the x tilt position the image was made with. """
        raise NotImplementedError

    def getDataPointsCount(self) -> int:
        """ Returns the number of valid data points/pixel in the image array. """
        raise NotImplementedError

    def getDataPointsCapacity(self) -> int:
        """ Returns the capacity of data points of the image array. """
        return int(np.prod(self.getResolution()))

    def getCompletion(self) -> float:
        """ Returns the completion percentage of the image. (0.0 to 1.0)"""
        return self.getDataPointsCount() / self.getDataPointsCapacity()

    def isCompleted(self) -> bool:
        """ Returns if the data image's data point capacity has been completely filled up or not. """
        return self.getDataPointsCount() == self.getDataPointsCapacity()

    def isEmpty(self) -> bool:
        """ Returns whether the image contains at least one scan data point or not. """
        return self.getDataPointsCount() == 0

    def getScanDate(self) -> datetime.datetime:
        """ Returns the date on which the data image has been created. """
        raise NotImplementedError

    def getScanDuration(self) -> datetime.timedelta:
        """ Returns the time the scan took to acquire all the data of the data image. """
        raise NotImplementedError

class ScanImage(IScanImage):
    """ Scan image with a maximum of 3 dimensions and a performance proven scan data point conversion. Inherit to create custom scan images. """

    """ The depth (3rd dimension size) of the image array. Redefine in subclasses for changes. """
    _IMAGE_ARRAY_DATA_DEPTH = 1

    """ The data type of the image array. Redefine in subclasses for changes. """
    _IMAGE_ARRAY_DATA_TYPE = int

    """ Single value to be filled as default value into the image array. Redefine in subclasses for changes. """
    _IMAGE_ARRAY_DEFAULT_VALUE = 0

    def __init__(self,
                 dataPoints: Iterable[IScanDataPoint],
                 position: Tuple[int, int],
                 size: Tuple[int, int],
                 resolution: Tuple[int, int],
                 laserIntensity: int,
                 zPosition: int,
                 xTilt: int,
                 scanDate: datetime.datetime,
                 scanDuration: datetime.timedelta,
                 intensity_multiplier=1):

        self._dataPointsCount = len(dataPoints)
        self._position = position
        self._size = size
        self._resolution = resolution
        self._laserIntensity = laserIntensity
        self._zPosition = zPosition
        self._xTilt = xTilt
        self._scanDate = scanDate
        self._scanDuration = scanDuration
        self._intensity_multiplier = intensity_multiplier

        self._imageArray = self._createImageArray(tuple(dataPoints))

    def getImageArray(self) -> np.ndarray:
        return self._imageArray

    def getDataPointsCount(self) -> int:
        return self._dataPointsCount

    def getResolution(self) -> Tuple[int, int]:
        return self._resolution

    def getSize(self) -> Tuple[int, int]:
        return self._size

    def getPosition(self) -> Tuple[int, int]:
        return self._position

    def getLaserIntensity(self) -> int:
        return self._laserIntensity

    def getZPosition(self) -> int:
        return self._zPosition

    def getXTilt(self) -> int:
        return self._xTilt

    def getScanDate(self) -> datetime.datetime:
        return self._scanDate

    def getScanDuration(self) -> datetime.timedelta:
        return self._scanDuration

    def _createImageArray(self, dataPoints: Sequence[IScanDataPoint]) -> np.ndarray:
        """ Creates and returns the underlying non object / real data `numpy.ndarray` from a `IScanDataPoint` sequence. """

        # work with reversed resolution since x values are row values which are of second dimension in terms of matrices
        reversedResolution = tuple(reversed(self.getResolution()))

        if self._IMAGE_ARRAY_DATA_DEPTH > 1:
            imageArray = np.full(reversedResolution + (self._IMAGE_ARRAY_DATA_DEPTH, ), self._IMAGE_ARRAY_DEFAULT_VALUE, self._IMAGE_ARRAY_DATA_TYPE)
        else:
            imageArray = np.full(reversedResolution, self._IMAGE_ARRAY_DEFAULT_VALUE, self._IMAGE_ARRAY_DATA_TYPE)

        if dataPoints:
            slices = np.frompyfunc(self.convertDataPoint, 1, self._IMAGE_ARRAY_DATA_DEPTH)(dataPoints)
            imageView = imageArray.view()

            if self._IMAGE_ARRAY_DATA_DEPTH > 1:
                imageView.shape = (np.prod(reversedResolution), self._IMAGE_ARRAY_DATA_DEPTH)

                for i in range(self._IMAGE_ARRAY_DATA_DEPTH):
                    imageView[:slices[i].size, i] = slices[i]
            else:
                imageView.shape = np.prod(reversedResolution)

                # Multi intensity multiplier disabled since xy data only yields one data point now
                # if self._intensity_multiplier > 1:
                #
                #     slices_use = []
                #     for index in range(math.ceil(len(slices) / self._intensity_multiplier)):
                #         low_range = (index*self._intensity_multiplier)
                #         temp_slices_use = slices[low_range: low_range + self._intensity_multiplier]
                #         slices_use.append(self.detect_latchup_condition(temp_slices_use))  # TEST
                #        # slices_use.append(temp_slices_use) #Pavan to test
                #
                #     imageView[:len(slices_use)] = slices_use
                # else:
                imageView[:slices.size] = slices

        return imageArray

    def convertDataPoint(self, dataPoint: IScanDataPoint):
        """ Converts a single data point to either a single or a data depth long sequence of values of the type specified by `ScanImage._IMAGE_ARRAY_DATA_TYPE`  """
        raise NotImplementedError

class ScanAreaConfig:
    """
        Immutable container of scan area and delay parameters (min/max/delay/stepsize of x/y).
        Modified for multi intensity  # TEST  # NEW
    """


    @staticmethod
    def createPointAreaScanAreaConfig(xPosition: int, yPosition: int):
        return ScanAreaConfig((xPosition, xPosition), (yPosition, yPosition), (1, 1), (0, 0))

    @staticmethod
    def createXLineAreaScanAreaConfig(xBounds: Tuple[int, int], yPosition: int, stepSize: int, stepDelay_ms: int):
        return ScanAreaConfig(xBounds, (yPosition, yPosition), (stepSize, 1), (stepDelay_ms, 0))

    @staticmethod
    def createYLineAreaScanAreaConfig(xPosition: int, yBounds: Tuple[int, int], stepSize: int, stepDelay_ms: int):
        return ScanAreaConfig((xPosition, xPosition), yBounds, (1, stepSize), (0, stepDelay_ms))

    def __init__(self,
                 xBounds: Tuple[int, int],
                 yBounds: Tuple[int, int],
                 stepSize: Tuple[int, int],
                 delayTime_ms: Tuple[int, int],
                 intensity_multiplier=None,  # TEST
                 ):

        self._bounds: Tuple[Tuple[int, int], Tuple[int, int]] = (xBounds, yBounds)
        self._stepSize: Tuple[int, int] = stepSize
        self._stepDelay_ms: Tuple[int, int] = delayTime_ms

        self._intensity_multiplier = 1 if intensity_multiplier is None else intensity_multiplier  # TEST
        
    @property
    def XBounds(self) -> Tuple[int, int]:
        """ Max and min x values. """
        return self._bounds[0]

    @property
    def YBounds(self) -> Tuple[int, int]:
        """ max and min y values. """
        return self._bounds[1]

    @property
    def XBoundsLow(self) -> int:
        return self._bounds[0][0]

    @property
    def XBoundsHigh(self) -> int:
        return self._bounds[0][1]

    @property
    def YBoundsLow(self) -> int:
        return self._bounds[1][0]

    @property
    def YBoundsHigh(self) -> int:
        return self._bounds[1][1]

    @property
    def MinPosition(self) -> Tuple[int, int]:
        """ Lowest position defined by this area configuration. """
        return (self.XBoundsLow, self.YBoundsLow)

    @property
    def MaxPosition(self) -> Tuple[int, int]:
        """ Highest position defined by this area configuration. """
        return (self.XBoundsHigh, self.YBoundsHigh)

    @property
    def StepSize(self) -> Tuple[int, int]:
        """ Step size in x and y direction. """
        return self._stepSize

    @property
    def XStepSize(self) -> int:
        return self._stepSize[0]

    @property
    def YStepSize(self) -> int:
        return self._stepSize[1]

    @property
    def DelayTime_ms(self) -> Tuple[int, int]:
        """ Delay times in x and y direction. """
        return self._stepDelay_ms

    @property
    def XStepDelay_ms(self) -> int:
        return self._stepDelay_ms[0]

    @property
    def YStepDelay_ms(self) -> int:
        return self._stepDelay_ms[1]

    @property
    def IsPointScan(self) -> bool:
        """ Whether the area to scan covers only a single point or not. """
        return self.XBoundsLow == self.XBoundsHigh and self.YBoundsLow == self.YBoundsHigh

    @property
    def IsLineScan(self) -> bool:
        """ Whether the area to scan cover only a single line or not. """
        return (self.XBoundsLow == self.XBoundsHigh and self.YBoundsLow != self.YBoundsHigh) \
            or (self.XBoundsLow != self.XBoundsHigh and self.YBoundsLow == self.YBoundsHigh)

    @property
    def IsAreaScan(self) -> bool:
        """ Whether the area to scan covers a rectangular area or not. """
        return self.XBoundsLow != self.XBoundsHigh and self.YBoundsLow != self.YBoundsHigh

    @property
    def ScanPositionsCount(self) -> int:
        """ The total number of scan points covered by this area configuration. """
        # return (self.ScanPositionsCountInX * self.ScanPositionsCountInY * self._intensity_multiplier) - \
        #        (self._intensity_multiplier - 1)  # TEST hardware weirdness

        # return self.ScanPositionsCountInX * self.ScanPositionsCountInY * self._intensity_multiplier

        return self.ScanPositionsCountInX * self.ScanPositionsCountInY



    @property
    def ScanPositionsCountInX(self) -> int:
        """ The total number of scan points in x direction. """
        # return math.ceil((self.XBoundsHigh - self.XBoundsLow) / self.XStepSize) + 1
        return math.floor((self.XBoundsHigh - self.XBoundsLow) / self.XStepSize) + 1  # TEST FIX

    @property
    def ScanPositionsCountInY(self) -> int:
        """ The total number of scan points in y direction. """
        # return math.ceil((self.YBoundsHigh - self.YBoundsLow) / self.YStepSize) + 1
        return math.floor((self.YBoundsHigh - self.YBoundsLow) / self.YStepSize) + 1  # TEST FIX


    @property  # NEW  NOT USED (DO NOT USE)
    def ScanPositionsCountInI(self) -> int:  # TEST
        """ The total number of scan points in y direction. """
        return math.floor((self.YBoundsHigh - self.YBoundsLow) / self.YStepSize) + 1

    @property
    def ScanResolution(self) -> Tuple[int, int]:
        """ The total number of scan points in x and y direction. """
        return (self.ScanPositionsCountInX, self.ScanPositionsCountInY)



    @property
    def IntensityMultiplier(self):  # TEST  # NEW
        return self._intensity_multiplier

    @property
    def ScanImageSize(self) -> Tuple[int, int]:
        """ The total length covered by this area configuration in x and y direction. """
        return (self.ScanPositionsCountInX * self.XStepSize, self.ScanPositionsCountInY * self.YStepSize)

    @property
    def XDistance(self) -> int:
        """ Total distance in x. """
        return self.XBoundsHigh - self.XBoundsLow

    @property
    def YDistance(self) -> int:
        """ Total distance in y. """
        return self.YBoundsHigh - self.YBoundsLow

    @property
    def ScanSize(self) -> Tuple[int, int]:
        """ Total distance in x and y direction. """
        return (self.XDistance, self.YDistance)

    @property
    def TotalDelayTime_ms(self) -> int:
        """ The total accumulated delay time in x and y direction. """
        return self.ScanPositionsCountInX * self.XStepDelay_ms + self.ScanPositionsCountInY * self.YStepDelay_ms

    def configureDlts(self, dltsConnection: DltsConnection):
        """ Sends the configuration data to the given DLTS connection. """
        dltsConnection.commandSet(DltsCommand.SetScanXAxisLowBoundary(self.XBoundsLow))
        dltsConnection.commandSet(DltsCommand.SetScanXAxisHighBoundary(self.XBoundsHigh))
        dltsConnection.commandSet(DltsCommand.SetScanYAxisLowBoundary(self.YBoundsLow))
        dltsConnection.commandSet(DltsCommand.SetScanYAxisHighBoundary(self.YBoundsHigh))

        dltsConnection.commandSet(DltsCommand.SetScanXStepSize(self.XStepSize))
        dltsConnection.commandSet(DltsCommand.SetScanYStepSize(self.YStepSize))

        dltsConnection.commandSet(DltsCommand.SetScanXDelay(self.XStepDelay_ms))
        dltsConnection.commandSet(DltsCommand.SetScanYDelay(self.YStepDelay_ms))

class IScan(INamed):
    """ Base interface for all DLTS scans. """

    def isRunning(self) -> bool:
        """ Returns if the scan is currently running. """
        raise NotImplementedError

    def isAborted(self) -> bool:
        """ Returns if the scan has been finished by aborting. """
        raise NotImplementedError

    def isFinished(self) -> bool:
        """ Returns if the scan has finished no matter how (Even aborted means finished). """
        raise NotImplementedError

    def isCompleted(self) -> bool:
        """ Returns if the scan has acquired all possible data points. """
        return self.isFinished() and self.getScannedPointsCount() >= self.getScanPointsCount()

    def getStartTime(self) -> datetime.datetime:
        """ Retuns the time the scan has been started. """
        raise NotImplementedError

    def getDuration(self) -> datetime.timedelta:
        """ Returns the amount of time the scan took. """
        raise NotImplementedError

    def getDataPoints(self) -> Tuple[IScanDataPoint]:
        """ Returns all currently acquired scan data points by the scan. Should also work at scan runtime and return a partial result. """
        raise NotImplementedError

    def getScanImages(self) -> Tuple[IScanImage]:
        """ Returns the resulting scan images of the scan. Should also work at scan runtime and return a partial result. """
        raise NotImplementedError

    def getScannedPointsCount(self) -> int:
        """ Returns the number of scan data points the scan has received.  """
        return len(self.getDataPoints())

    def getScanPointsCount(self) -> int:
        """ Returns the number of total scan data points the scan can possibly receive. """
        raise NotImplementedError

    def getProgressPercentage(self) -> float:
        """ Returns the current progess percentage of the scan. (0.0 - 1.0) """
        return self.getScannedPointsCount() / self.getScanPointsCount() if self.getScanPointsCount() is not None else 0.0

    def start(self, dltsConnection: DltsConnection):
        """ Starts the scan using the provided DLTS connection. """
        raise NotImplementedError

    def abort(self):
        """ Aborts the scan. """
        raise NotImplementedError

class IPausableScan(IScan):
    """ DLTS scan which can be paused. """

    def isPaused(self) -> bool:
        """ Returns if the scan is pausing. """
        raise NotImplementedError

    def pause(self):
        """ Pauses the scan. """
        raise NotImplementedError

    def resume(self):
        """ Resumes the scan. """
        raise NotImplementedError

class Scan(IScan):
    """ Scan implementation which uses a additional threads and is based on custom commands.

    The standard scan class provides a basic implemenation of the scan behaviour and uses a additional threads to communicate with the DLTS
    and create acquired scan images. Inheriting from this class requires an implementation of at least one custom `ScanImage` class.
    Furthermore the commanding of the DLTS to start and abort the scan and to receive a data point have to be implemented.

    Parameters
    ----------
    config: `ScanAreaConfig`
        The area to scan including delays
    positioningTime_ms: `int` (default: `0`)
        The time the scan waits until the DLTS has moved to its scan start position.
    xTilt: `int` (default: `None`)
        The x tilt position during scanning. If `None` it is ignored.
    zPosition: `int` (default: `None`)
        The z position during scanning. If `None` it is ignored.
    laserIntensity: `int` (default: `None`)
        The laser intensity during scanning. If `None` it is ignored.
    """

    """ Interval in which the scan images creation creates the scan's scan images. """
    _SCAN_IMAGES_CREATION_INTERVAL_S = 5.

    def __init__(
            self,
            config: ScanAreaConfig,
            positioningTime_ms: int = 0,
            xTilt: int = None,
            zPosition: int = None,
            laserIntensity: int = None,
            autoFocus=None,  # NEW
            laserMinIntensity=None,
            laserMaxIntensity=None,# NEW
            laserStepIntensity=None,  # NEW
    ):

        self._configuration = config
        self._positioningTime_ms = positioningTime_ms
        self._xTilt = xTilt
        self._zPosition = zPosition
        self._laserIntensity = laserIntensity
        self._autoFocus = autoFocus  # NEW
        self._laserMinIntensity = laserMinIntensity
        self._laserMaxIntensity = laserMaxIntensity        # NEW
        self._laserStepIntensity = laserStepIntensity  # NEW

        self._dltsConnection = None

        self._scanImages: Tuple[IScanImage] = tuple()
        self._dataPoints: List[ScanDataPoint] = list()

        self._startTime: datetime.datetime = None
        self._finishTime: datetime.datetime = None

        self._scanFinished = False
        self._abortRequested = False
        self._scanningForDataPoints = False

        self._dataPointsLock = threading.Lock()
        self._scanImagesLock = threading.Lock()

        self._scanThread = threading.Thread(target=self._scanThreadTarget)
        self._scanImagesCreationThread = threading.Thread(
            target=self._scanImagesCreationThreadTarget)

    def getAreaConfig(self) -> ScanAreaConfig:
        """ Returns the scan area configuration of the scan. """
        return self._configuration

    def getPositioningTime_ms(self) -> int:
        """ Returns the optional positioning time of the scan. """
        return self._positioningTime_ms

    def getXTilt(self) -> int:
        """ Returns the optional x tilt position which was active during scanning. """
        return self._xTilt

    def getZPosition(self) -> int:
        """ Returns the optional z position which was active during scanning. """
        return self._zPosition

    def getLaserIntensity(self) -> int:
        """ Returns the laser intensity which was active during scanning. """
        return self._laserIntensity

    def getDataPoints(self) -> Tuple[ScanDataPoint]:
        with self._dataPointsLock:
            dataCopy = tuple(self._dataPoints)
        return dataCopy

    def getScannedPointsCount(self) -> int:
        with self._dataPointsLock:
            length = len(self._dataPoints)
        return length

    def isRunning(self) -> bool:
        return self._scanThread.is_alive()

    def isAborted(self) -> bool:
        return self.isFinished() and self._abortRequested

    def isFinished(self) -> bool:
        return self._scanFinished and not self._scanThread.is_alive()

    def getStartTime(self) -> datetime.datetime:
        return self._startTime

    def getDuration(self) -> datetime.timedelta:
        return datetime.datetime.now() - self._startTime if self.isRunning() else self._finishTime - self._startTime if self.isFinished() else datetime.timedelta()

    def getScanImages(self) -> Tuple[IScanImage]:
        with self._scanImagesLock:
            scanImages = tuple(self._scanImages)
        return scanImages

    def getScanPointsCount(self) -> int:
        ret_val = self._configuration.ScanPositionsCount
        return self._configuration.ScanPositionsCount

    def start(self, dltsConnection: DltsConnection):
        if not self.isRunning() and not self.isFinished():
            self._dltsConnection = dltsConnection

            self._scanThread.start()

    def abort(self):
        if self.isRunning() and self._scanningForDataPoints:
            self._abortRequested = True

    def _scanThreadTarget(self):
        """ Target method of the scan thread which manages communication and acquires data points. """


        self._startTime = datetime.datetime.now()

        with self._dltsConnection as dltsConnection:

            cachedXTilt = None
            cachedZPosition = None
            cachedLaserIntensity = None

            try:
                cachedXTilt = dltsConnection.commandGetUInt16(DltsCommand.GetXTilt())
                cachedZPosition = dltsConnection.commandGetUInt16(DltsCommand.GetZPosition())
                cachedLaserIntensity = dltsConnection.commandGetUInt16(DltsCommand.GetLaserIntensity())

                if self._xTilt is None:
                    self._xTilt = cachedXTilt
                if self._zPosition is None:
                    self._zPosition = cachedZPosition
                if self._laserIntensity is None:
                    self._laserIntensity = cachedLaserIntensity

                dltsConnection.commandSet(DltsCommand.SetXTilt(self._xTilt))
                dltsConnection.commandSet(DltsCommand.SetZPosition(self._zPosition))
                dltsConnection.commandSet(DltsCommand.SetLaserIntensity(self._laserIntensity))

                self._configuration.configureDlts(dltsConnection)

                dltsConnection.commandSet(DltsCommand.SetXPosition(self._configuration.XBoundsLow))
                dltsConnection.commandSet(DltsCommand.SetYPosition(self._configuration.YBoundsLow))

                time.sleep(self._positioningTime_ms / 1000)

                if self._laserMinIntensity is not None:  # NEW
                    from dltscontrol.color_print import cprint
                    cprint(f'    _laserMinIntensity', 'debug_w')
                    if hasattr(self, 'setScanLaserMinIntensity'):
                        self.setScanLaserMinIntensity(dltsConnection, self._laserMinIntensity)

                if self._laserMaxIntensity is not None:  # NEW
                    from dltscontrol.color_print import cprint
                    cprint(f'    _laserMaxIntensity', 'debug_w')
                    if hasattr(self, 'setScanLaserMaxIntensity'):
                        self.setScanLaserMaxIntensity(dltsConnection, self._laserMaxIntensity)

                if self._laserStepIntensity is not None:  # NEW
                    from dltscontrol.color_print import cprint
                    cprint(f'    _laserStepIntensity', 'debug_w')
                    if hasattr(self, 'setScanLaserStepIntensity'):
                        self.setScanLaserStepIntensity(dltsConnection, self._laserStepIntensity)

                if self._autoFocus:  # NEW
                    from dltscontrol.color_print import cprint
                    if hasattr(self, 'setAutoFocus'):
                        cprint(f'    AUTO FOCUS', 'debug_w')
                        self.setAutoFocus(dltsConnection)
                        # Forces read all data after this (3 bytes of unused data error)
                        extra_data = dltsConnection.readAll()
                        if extra_data:
                            cprint(f'extra_data = {extra_data}', 'debug_r')


                from dltscontrol.color_print import cprint
                cprint(f'TEST SCAN', 'debug_b')
                # time.sleep(100)

                self.onScanStart(dltsConnection)

                self._scanningForDataPoints = True

                # start scan image creation in seperate thread
                self._scanImagesCreationThread.start()

                while self._scanningForDataPoints:






                    dataPoint = self.onReceiveDataPoint(dltsConnection)

                    with self._dataPointsLock:
                        self._dataPoints.append(dataPoint)

                    if self._abortRequested:
                        self.onScanAbort(dltsConnection)

                    cprint(f'{self.getScannedPointsCount()} of {self.getScanPointsCount()}', 'debug_w')

                    if self._abortRequested or self.getScannedPointsCount() >= self.getScanPointsCount():
                        cprint(f'STOP', 'debug_g')
                        self._scanningForDataPoints = False

            except Exception as ex:
                logger.exception("Scan run has failed. Reason: %s", ex)
            finally:
                # make sure scan images creation thread will terminate
                self._scanningForDataPoints = False

                try:
                    if cachedXTilt is not None:
                        dltsConnection.commandSet(DltsCommand.SetXTilt(cachedXTilt))
                    if cachedZPosition is not None:
                        dltsConnection.commandSet(DltsCommand.SetZPosition(cachedZPosition))
                    if cachedLaserIntensity is not None:
                        dltsConnection.commandSet(DltsCommand.SetLaserIntensity(cachedLaserIntensity))
                except Exception as ex:
                    logger.exception("Scan could not reset optional scan parameters. Reason: %s", ex)

        # wait until most recent scan images have benn created
        if self._scanImagesCreationThread.is_alive():
            self._scanImagesCreationThread.join()

        self._finishTime = datetime.datetime.now()
        self._scanFinished = True

    def _scanImagesCreationThreadTarget(self):
        """ Target of scan images creation thread. """
        try:
            scanImagesDirty = True

            while scanImagesDirty:

                scanImagesDirty = self._scanningForDataPoints

                # avoid two acquired locks at the same time to eliminate any deadlock risk
                scanImages = self.createScanImages(self.getDataPoints())

                with self._scanImagesLock:
                    self._scanImages = scanImages

                time.sleep(self._SCAN_IMAGES_CREATION_INTERVAL_S)
        except Exception as ex:
            logger.exception("Scan images creation has failed. Reason: %s", ex)

    def createScanImages(self, dataPoints: Tuple[IScanDataPoint]) -> Sequence[IScanImage]:
        """ Creates the scan's scan images from the current scan's data points. Gets called from the scan images creation thread. """
        print("in createScanImages")
        raise NotImplementedError

    def onScanStart(self, dltsConnection: DltsConnection):
        """ Called when the scan shall be started. Make sure to send the necessary commands to the DLTS. Gets called from the scan thread. """
        raise NotImplementedError

    def onScanAbort(self, dltsConnection: DltsConnection):
        """ Called when the scan shall be aborted. Make sure to send the necessary commands to the DLTS. Gets called from the scan thread. """
        raise NotImplementedError

    def onReceiveDataPoint(self, dltsConnection: DltsConnection) -> IScanDataPoint:
        """ Called when the scan shall receive and return a single scan data point. Make sure to send the necessary commands to the DLTS. Gets called from the scan thread.  """
        raise NotImplementedError

class DltsControlFlowError(DltsException):
    pass

class Dlts:
    """ High level DLTS interface. Keeps track of running and finished scans.

    Parameters
    ----------
    dltsConnection: `DltsConnection`
        The DLTS connection to work with.
    scanHistorySize: `int` (default: `1`)
        The number of scans which are kept stored after they have been finished. (LIFO buffer size)
    """
    def __init__(self, dltsConnection: DltsConnection, scanHistorySize: int = 1):
        self._dltsConnection: DltsConnection = dltsConnection
        self._scan: IScan = None
        self._scanHistory = deque([], scanHistorySize)

    @property
    def IsConnected(self):
        """ Whether the DLTS connection is open or not. """
        return self._dltsConnection is not None and self._dltsConnection.IsOpen

    @property
    def DltsConnection(self) -> DltsConnection:
        """ The underlying DLTS connection. """
        return self._dltsConnection

    @DltsConnection.setter
    def DltsConnection(self, connection: DltsConnection):
        if self.IsConnected and self.IsScanRunning:
            raise DltsControlFlowError("A connection change can't be executed during a running scan.")

        self._dltsConnection = connection

    @property
    def _DltsConnection(self) -> DltsConnection:
        """ Communication safe dlts connection. """
        if not self.IsConnected:
            raise DltsControlFlowError("Can't command the DLTS if its not connected.")
        if self.IsScanRunning:
            raise DltsControlFlowError("Can't command the DLTS while it is running a scan.")

        return self._dltsConnection

    @property
    def Scan(self) -> IScan:
        """ The most recent scan that has been started. """
        return self._scan

    @property
    def IsScanRunning(self) -> bool:
        """ If the most recent started scan is still running. """
        return self._scan is not None and self._scan.isRunning()

    @property
    def ScanHistory(self) -> Sequence[IScan]:
        """ The LIFO scan history of finished scans. """
        return self._scanHistory

    def setX(self, x: int):
        """ Sets the x position of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetXPosition(x))

    def getX(self):
        """ Returns the x position of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetXPosition())

    def setY(self, y: int):
        """ Sets the y position of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetYPosition(y))

    def getY(self):
        """ Returns the y position of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetYPosition())

    def setZ(self, z: int):
        """ Sets the z position of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetZPosition(z))

    def getZ(self):
        """ Returns the z position of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetZPosition())

    def setXTilt(self, xTilt: int):
        """ Sets the x tilt position of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetXTilt(xTilt))

    def getXTilt(self):
        """ Returns the x tilt position of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetXTilt())

    def getLaserReflectionValue(self) -> int:
        """ Returns the laser reflection value of the connected DLTS. """
        # Command is currently not implemented in the DLTS firmware but defined in the protocol
        # return self._DltsConnection.commandGetUInt8(DltsCommand.ActionScanPoint())

        #workaround
        value = -1

        with self._DltsConnection as dltsConnection:
            x, y = self.getX(), self.getY()

            scanAreaConfig = ScanAreaConfig.createPointAreaScanAreaConfig(x, y)
            scanAreaConfig.configureDlts(dltsConnection)

            value = dltsConnection.commandGetUInt8(DltsCommand.ActionScanArea())

            self.setX(x)
            self.setY(y)

        return value

    def setLaserIntensity(self, intensity: int):
        """ Sets the laser intensity of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetLaserIntensity(intensity))

    def getLaserIntensity(self):
        """ Returns the laser intensity of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetLaserIntensity())

    def setLaserPulseIntensity(self, intensity: int):
        """ Sets the laser pulse intensity of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetLaserPulseIntensity(intensity))

    def getLaserPulseIntensity(self) -> int:
        """ Returns the laser pulse intensity of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetLaserPulseIntensity())

    def setLaserPulseFrequency(self, frequency: int):
        """ Sets the laser pulse frequency of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetLaserPulseFrequency(frequency))

    def getLaserPulseFrequency(self) -> int:
        """ Returns the laser pulse frequency of the connected DLTS. """
        return self._DltsConnection.commandGetUInt16(DltsCommand.GetLaserPulseFrequency())

    def fireLaserPulse(self, intensity: int = None, frequency: int = None):
        """ Fires a laser pulse at the connected DLTS. Sets the provided pulse intensity and frequency beforehand if not `None`. """
        if intensity is not None:
            #self.setLaserPulseIntensity(intensity)
            self.setLaserPulseIntensity(2000)	#ToDo: nicht statisch!
        #if frequency is not None:
        #    self.setLaserPulseFrequency(frequency)	#no need to change freq for single pulse

        self._DltsConnection.commandWithAcknowledge(DltsCommand.ActionLaserPulse())

    # Probably the wrong spot for this method. Should be implemented by a Latchup-Scan. (Done but also left here for non scan experiements.)
    def SetLatchUpTurnOffDelay(self, milliSeconds: int):
        """ Sets the latchup turn off delay of the connected DLTS. """
        self._DltsConnection.commandSet(DltsCommand.SetLatchUpTurnOffDelayMilliseconds(milliSeconds))
        self._DltsConnection.commandSet(DltsCommand.SetLatchUpTurnOffDelayMicroseconds(microSeconds))

    def startScan(self, scan: IScan):
        """ Starts the given scan and moves the current into the history buffer if there is one. """
        if self.IsScanRunning:
            raise DltsControlFlowError("Can't run two scans at the same time.")

        if self._scan is not None:
            self._scanHistory.appendleft(self._scan)

        self._scan = scan

        self._scan.start(self._DltsConnection)

class ByteStreamBasedDltsConnection(DltsConnection):
    """ Classic byte stream (`RawIOBase`) based DLTS Connection implementation. """

    def __init__(self, byteStream: RawIOBase):
        super().__init__()

        self._byteStream = byteStream

    @property
    def _IsOpenUnlocked(self) -> bool:
        return not self._byteStream.closed

    def _closeUnlocked(self):
        self._byteStream.close()

    def _writeUnlocked(self, data: bytes) -> int:
        return self._byteStream.write(data)

    def _readUnlocked(self, size = 1) -> bytes:
        return self._byteStream.read(size)

    def _readAllUnlocked(self):
        return self._byteStream.readall()
