import copy
from .exceptions import ArduMgrError


class Programmer(object):
    """
    Programmer is a tool use for these tasks:

    1. Upload binary program to your board
    2. Flash erase/dump/write
    3. Board configuration change or reading
    """

    def __init__(self, platform):
        """
        You must predefined these preferences before create a programmer
        (for ex):

        ardumgr.programmer=usbtinyisp
        ardumgr.board=mega
        ardumgr.cpu=atmega2560
        ardumgr.serial.port=/dev/ttyUSB0

        They will expanded to these preferences (Arduino IDE required):

        programmer=arduino:usbtinyisp
        board=mega
        custom_cpu=mega_atmega2560
        serial.port=/dev/ttyUSB0
        """

        self._platform = copy.deepcopy(platform)
        platform = self._platform  # Use new created platform

        self._programmer = platform.cfgs["ardumgr.programmer"]
        self._board = platform.cfgs["ardumgr.board"]
        self._cpu = platform.cfgs["ardumgr.cpu"]
        self._serial_port = platform.cfgs["ardumgr.serial.port"]

        # Convert preferences to Arduino IDE required format
        platform.cfgs["programmer"] = "arduino:%s" % self._programmer
        platform.cfgs["board"] = self._board
        platform.cfgs["custom_cpu"] = "%s_%s" % (self._board, self._cpu)
        platform.cfgs["serial.port"] = self._serial_port

        # Check if cpu related to specfic board
        cpus = platform.get_board_supported_cpus(self._board)
        if cpus:
            if self._cpu is None:
                raise ArduMgrError(
                    "You must specific a cpu for board \"%s\"! Choice : %s" % (
                        self._board, cpus))
            elif self._cpu not in cpus:
                raise ArduMgrError(
                    "Board \"%s\" don't support cpu \"%s\"!" % (self._board, self._cpu))
        elif self._cpu is not None:
            raise ArduMgrError(
                "Board have a default cpu, don't specfic it yourself!" % self._board)

        # Specific serial port settings if it valid
        if self._serial_port:
            platform.cfgs["serial.port"] = self._serial_port

        # Find board and cpu specific configs and expand it to our platform
        key = "boards.%s" % self._board
        subtree = platform.cfgs.get_subtree(key)
        platform.cfgs.update(subtree)

        if self._cpu:
            key = "boards.%s.menu.cpu" % self._board
            subtree = platform.cfgs.get_subtree(key)
            platform.cfgs.update(subtree)

        # Expand upload tool configs
        upload_tool = platform.cfgs["upload.tool"]
        subtree = platform.cfgs.get_subtree("tools.%s" % upload_tool)
        platform.cfgs.update(subtree)
