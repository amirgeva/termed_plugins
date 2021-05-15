from subprocess import Popen, PIPE
import config
from geom import Point
from plugin import WindowPlugin
from logger import logwrite


class MakerPlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(0, 10))
        self._root = config.get_value('root')
        self._offset = 0
        self._lines = []

    def action_make(self):
        logwrite(f'Make in {self._root}')
        self._lines = []
        p = Popen(['make'], stdout=PIPE, stderr=PIPE, cwd=self._root)
        for line in p.stdout:
            self._lines.append(line.decode('utf-8'))
            self.render()

    def render(self):
        super().render()
        w = self.get_window().width()
        for y in range(self.get_window().height()):
            i = self._offset + y
            line = ' ' * w
            if i < len(self._lines):
                line = self._lines[i]
                if len(line) > w:
                    line = line[0:w]
                if len(line) < w:
                    line = line + ' ' * (w - len(line))
            self._window.set_cursor(0, y)
            self._window.text(line, 1)
