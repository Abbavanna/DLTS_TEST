""" 
Extension which adds an serial connection based `DltsService`.

Implementations
---------------
`SerialDltsService`
"""
from serial import Serial

from dltscontrol.apptk import Service, ComponentRequestAbortedError
from dltscontrol.dlts import DltsConnection, ByteStreamBasedDltsConnection

# extension dependencies
from dltscontrol.app.core import rootLogger, DltsService, IUserConfigComponent
from dltscontrol.app.serial import SerialDialog

class SerialDltsService(DltsService, IUserConfigComponent):
    """ Service which provides access to a DLTS over a serial interface. """

    _USER_CONFIG_DLTS_SECTION = "Dlts Serial"

    _USER_CONFIG_BAUDRATE_KEY = "baudrate"
    _USER_CONFIG_BYTESIZE_KEY = "bytesize"
    _USER_CONFIG_STOPBITS_KEY = "stopbits"
    _USER_CONFIG_PARITY_KEY = "parity"
    _USER_CONFIG_TIMEOUT_KEY = "timeout"

    _USER_CONFIG_BAUDRATE_DEFAULT = 115200
    _USER_CONFIG_BYTESIZE_DEFAULT = 8
    _USER_CONFIG_STOPBITS_DEFAULT = 1
    _USER_CONFIG_PARITY_DEFAULT = "None"
    _USER_CONFIG_TIMEOUT_DEFAULT = 1000

    def _openSerialDialog(self) -> SerialDialog:
        serialDialog = self.getContext().openDialog(SerialDialog)

        userConfig = self.getUserConfig()

        if userConfig is not None:
            baudrate = int(userConfig.getSet(self._USER_CONFIG_DLTS_SECTION, self._USER_CONFIG_BAUDRATE_KEY, self._USER_CONFIG_BAUDRATE_DEFAULT))
            byteSize = int(userConfig.getSet(self._USER_CONFIG_DLTS_SECTION, self._USER_CONFIG_BYTESIZE_KEY, self._USER_CONFIG_BYTESIZE_DEFAULT))
            stopBits = userConfig.getSet(self._USER_CONFIG_DLTS_SECTION, self._USER_CONFIG_STOPBITS_KEY, self._USER_CONFIG_STOPBITS_DEFAULT)
            parityName = userConfig.getSet(self._USER_CONFIG_DLTS_SECTION, self._USER_CONFIG_PARITY_KEY, self._USER_CONFIG_PARITY_DEFAULT)
            timeOut = int(userConfig.getSet(self._USER_CONFIG_DLTS_SECTION, self._USER_CONFIG_TIMEOUT_KEY, self._USER_CONFIG_TIMEOUT_DEFAULT))

            try:
                stopBits = int(stopBits)
            except:
                stopBits = float(stopBits)

            serialDialog.SerialConfigurationPanel.setBaudrate(baudrate)
            serialDialog.SerialConfigurationPanel.setBytesize(byteSize)
            serialDialog.SerialConfigurationPanel.setStopbits(stopBits)
            serialDialog.SerialConfigurationPanel.setParityName(parityName)
            serialDialog.SerialConfigurationPanel.setTimeOut_ms(timeOut)
        
        return serialDialog

    def _createDltsConnection(self) -> DltsConnection:
        serial = self._openSerialDialog().waitForResult()

        if serial is None:
            raise ComponentRequestAbortedError("Serial connection dialog has been aborted.")
        
        if not serial.isOpen():
            serial.open()

        return ByteStreamBasedDltsConnection(serial)
        
# extension area

from dltscontrol.app.manifest import manifest

# services
manifest.insert(SerialDltsService, _global = True)