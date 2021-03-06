import subprocess
import os.path
from pathlib import Path
from .exceptions import ArduMgrError
from .configs import ConfigsMgr


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
        ardumgr.serial_port=/dev/ttyUSB0

        They will expanded to these preferences (Arduino IDE required):

        programmer=arduino:usbtinyisp
        board=mega
        custom_cpu=mega_atmega2560
        serial.port=/dev/ttyUSB0
        """

        self._platform = platform
        self._cfgs = ConfigsMgr()
        self._cfgs.base_on(platform.cfgs)

        self._programmer = self._cfgs["ardumgr.programmer"]
        self._board = self._cfgs["ardumgr.board"]
        self._cpu = self._cfgs["ardumgr.cpu"]
        self._serial_port = self._cfgs["ardumgr.serial_port"]

        # Check if cpu related to specfic board
        cpus = platform.get_board_supported_cpus(self._board)
        if cpus:
            if self._cpu is None:
                raise ArduMgrError(
                    "You must specific a cpu for board \"%s\"! Choice : %s" % (
                        self._board, cpus))
            elif self._cpu not in cpus:
                raise ArduMgrError(
                    "Board \"%s\" don't support cpu \"%s\"!" % (
                        self._board, self._cpu))
        elif self._cpu is not None:
            raise ArduMgrError(
                "Board have a default cpu, don't specfic it yourself!"
                % self._board)

        # Find board and cpu specific configs and expand it to our platform
        key = "boards.%s" % self._board
        subtree = self._cfgs.get_subtree(key)
        self._cfgs.update(subtree)

        if self._cpu:
            key = "boards.%s.menu.cpu.%s" % (self._board, self._cpu)
            subtree = self._cfgs.get_subtree(key)
            self._cfgs.update(subtree)

        # Expand upload tool configs
        upload_tool = self._cfgs["upload.tool"]
        subtree = self._cfgs.get_tool_subtree(upload_tool)
        self._cfgs.update(subtree)

        # Expand programmer's configs
        subtree = self._cfgs.get_subtree("programmers.%s" % self._programmer)
        self._cfgs.update(subtree)

    def _generate_upload_pattern(self, build_path, project_name):
        cfgs = ConfigsMgr()
        cfgs.base_on(self._cfgs)

        if build_path is not None:
            cfgs["build.path"] = build_path

        if project_name is not None:
            cfgs["build.project_name"] = project_name

        return cfgs.get_expanded("upload.pattern")

    def _generate_program_pattern(self, build_path, project_name):
        cfgs = ConfigsMgr()
        cfgs.base_on(self._cfgs)

        if build_path is not None:
            cfgs["build.path"] = build_path

        if project_name is not None:
            cfgs["build.project_name"] = project_name

        return cfgs.get_expanded("upload.pattern")

    def upload(self, build_path=None, project_name=None):
        pattern = self._generate_upload_pattern(build_path, project_name)
        return subprocess.call(pattern, shell=True)

    def upload_bin(self, binary_file_path):
        path = Path(binary_file_path)
        return self.upload(path.parent, os.path.splitext(path.name)[0])
