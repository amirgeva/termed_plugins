import os
import config
import logger
from geom import Point
from plugin import WindowPlugin
from logger import logwrite
from menus import Menu, fill_menu
from dialogs.file_dialog import FileDialog
from .treenode import TreeNode, convert_tree
from .cmake_utils import scan_cmake


class DirTreePlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(20, 0))
        self._offset = 0
        self._search_term = ''
        self._search_results = []
        self._result_index = 0
        self._node_order = {}
        self._root = os.getcwd()
        self._tree = TreeNode('', True, None)
        self.scan(self._tree, self._root, 0)
        self._root = config.get_value('root')
        if self._root:
            self.select_root(self._root)
        self._total_rows = 0
        self._cur_y = -1
        if self._tree.child_count() > 0:
            self._cur_y = 0
        self.create_menu()

    def select_root(self, root):
        self._root = root
        makefile_path = os.path.join(root, 'Makefile')
        using_makefile = False
        if os.path.exists(makefile_path):
            using_makefile = self.select_makefile(root, makefile_path)
        if not using_makefile:
            self._tree = TreeNode('', True, None)
            self.scan(self._tree, self._root, 0)

    def select_makefile(self, build_folder: str, path: str):
        self._root, tree = scan_cmake(build_folder, path)
        logger.logwrite(f'Makefile Tree:\n{tree}\n------------------------------\n')
        self._tree = convert_tree(tree)
        return True

    def scan(self, tree, path: str, indent: int):
        spaces = ' ' * indent
        entry: os.DirEntry
        for entry in os.scandir(path):
            if not entry.name.startswith('.'):
                if entry.is_dir(follow_symlinks=False):
                    node = TreeNode(entry.name, True, tree)
                    tree.add_child(node)
                    logwrite(f'{spaces}{entry.name}/')
                    self.scan(node, os.path.join(path, entry.name), indent + 2)
                if entry.is_file(follow_symlinks=False):
                    tree.add_child(TreeNode(entry.name, False, tree))
                    logwrite(f'{spaces}{entry.name}')

    def _render_node(self, node: TreeNode, indent: int, y: int):
        spaces = ' ' * indent
        for child in node:
            self._node_order[y] = child
            if 0 <= y < self._window.height() and indent < self._window.width():
                self._window.set_cursor(0, y)
                w = self._window.width() - indent - 1
                text = child.get_name()
                if len(text) > w:
                    text = text[0:w]
                if len(text) < w:
                    text = text + ' ' * (w - len(text))
                prefix = ' '
                if child.is_dir():
                    prefix = '^' if child.is_expanded() else '>'
                color = 1
                if y == self._cur_y:
                    color = 2
                self._window.text(spaces, color)
                self._window.text(prefix, color)
                self._window.text(text, color)
                y = y + 1
                if child.is_dir() and child.is_expanded():
                    y = self._render_node(child, indent + 1, y)
            else:
                y = y + 1
        return y

    def render(self):
        super().render()
        self._node_order = {}
        y = self._render_node(self._tree, 0, -self._offset)
        self._total_rows = y + self._offset
        spaces = ' ' * self._window.width()
        while y < self._window.height():
            self._window.set_cursor(0, y)
            self._window.text(spaces, 1)
            y = y + 1

    def on_focus(self):
        super().on_focus()
        config.get_app().cursor(False)

    def action_move_left(self):
        if self._cur_y in self._node_order:
            node = self._node_order.get(self._cur_y)
            p = node.get_parent()
            if p and p.is_dir():
                for y in sorted(self._node_order.keys()):
                    if self._node_order.get(y) is p:
                        self._cur_y = y
                        p.set_expanded(False)
                        break

    def action_move_down(self):
        if self._cur_y < (self._total_rows - 1):
            self._cur_y += 1
            self._ensure_visible()

    def action_move_up(self):
        if self._cur_y > 0:
            self._cur_y -= 1
            self._ensure_visible()

    def _ensure_visible(self):
        dy = self._cur_y - self._offset
        h = self._window.height()
        if dy < 0 or dy >= h:
            self._offset = self._cur_y - h // 2
            self.render()

    def action_enter(self):
        if self._search_term:
            self.perform_search()
            self._search_term = ''
        elif self._cur_y in self._node_order:
            cur_node = self._node_order.get(self._cur_y)
            if cur_node.is_dir():
                cur_node.toggle_expand()
            else:
                config.get_app().open_file(cur_node.get_path(self._root))

    def dfs_search(self, node: TreeNode, term: str):
        results = []
        for child in node:
            if child.is_dir():
                results.extend(self.dfs_search(child, term))
            else:
                if term in child.get_name():
                    results.append(child)
        return results

    def clear_search(self):
        self._search_term = ''

    def process_text_key(self, key: str):
        self._search_term += key

    def perform_search(self):
        self._search_results = self.dfs_search(self._tree, self._search_term)
        self._search_results.sort(key=lambda x: x.get_name())
        self._search_results.sort(key=lambda x: x.get_path(self._root).count('/'))
        self._result_index = 0
        self.show_search_result()

    def show_search_result(self):
        if self._search_results:
            res = self._search_results[self._result_index]
            res.expand_tree()
            self.render()
            for y in sorted(self._node_order.keys()):
                node = self._node_order.get(y)
                if node is res:
                    self._cur_y = y
                    break

    def action_find_replace_next(self):
        if self._search_results:
            self._result_index = (self._result_index + 1) % len(self._search_results)
            self.show_search_result()

    def process_key(self, key: str):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)
            else:
                self.clear_search()
        else:
            self.clear_search()

    def on_action(self, action: str):
        super().on_action(action)
        self.clear_search()

    def action_select_root(self):
        d = FileDialog('SelDir')
        config.get_app().set_focus(d)
        config.get_app().event_loop(True)
        r = d.get_result()
        if r == 'Select':
            config.set_value('root',d.directory.text)
            self.select_root(d.directory.text)

    def create_menu(self):
        desc = [('&File', [('&Root Dir   Ctrl+O', self, 'select_root')
                           ]),
                ('&Options', [('&General', self, 'general_settings')
                              ]),
                ]
        bar = Menu('')
        fill_menu(bar, desc)
        self.set_menu(bar)
