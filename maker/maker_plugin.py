import re
import subprocess as sp
import config
from geom import Point
from plugin import WindowPlugin
from logger import logwrite


class MakerPlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(0, 10))
        self._root = config.get_value('root')
        self._offset = 0
        self._error_index = 0
        self._lines = []
        self._error_pattern = re.compile(r'^([/.\w]+):(\d+):(\d+): error')

    def global_action_make(self):
        return self.action_make()

    def action_make(self):
        logwrite(f'Make in {self._root}')
        self._lines = []
        p = sp.Popen(['make'], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self._root)
        for line in p.stdout:
            self._lines.append(line.decode('utf-8').rstrip())
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

    def action_move_down(self):
        self._offset += 1

    def action_move_up(self):
        if self._offset > 0:
            self._offset -= 1

    def global_action_next_error(self):
        return self.action_next_error()

    def action_next_error(self):
        source_root = config.get_value('source_root')
        while self._error_index < len(self._lines):
            line = self._lines[self._error_index]
            self._error_index += 1
            m = re.search(self._error_pattern, line)
            if m:
                try:
                    g = m.groups()
                    path = g[0]
                    row = int(g[1])
                    col = int(g[2])
                    if path.startswith(source_root):
                        config.get_app().open_file(path, row - 1, col - 1)
                except ValueError:
                    pass
                return
        self._error_index = 0
