import os
from subprocess import Popen, PIPE
from config import get_app
from geom import Point
from plugin import WindowPlugin
from dialogs.file_dialog import FileDialog


class MakerPlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(0, 10))
        self._makefile = ''

    def settings(self):
        d = FileDialog(True)
        get_app().modal_dialog(d)
        if d.get_result() == 'Load':
            self._makefile = d.get_path()

    def action_make(self):
        directory = os.path.dirname(self._makefile)
        p = Popen(['make', '-f', self._makefile], stdout=PIPE, stderr=PIPE, cwd=directory)
