import os
import config
from geom import Point
from plugin import WindowPlugin
from logger import logwrite


class TreeNode:
    def __init__(self, name: str, is_dir: bool, parent=None):
        self._name = name
        self._parent = parent
        if is_dir:
            self._name += "/"
        self._expanded = False
        self._is_dir = is_dir
        self._children = []
        self._current = 0

    def __iter__(self):
        self._current = 0
        return self

    def __next__(self):
        if self._current < len(self._children):
            self._current += 1
            return self._children[self._current - 1]
        raise StopIteration

    def get_parent(self):
        return self._parent

    def child_count(self) -> int:
        return len(self._children)

    def get_child(self, index: int):
        return self._children[index]

    def get_name(self) -> str:
        return self._name

    def is_dir(self) -> bool:
        return self._is_dir

    def is_expanded(self) -> bool:
        return self._expanded

    def toggle_expand(self):
        self._expanded = not self._expanded

    def set_expanded(self, state: bool):
        self._expanded = state

    def expand_tree(self):
        node = self
        while node.get_parent():
            node = node.get_parent()
            node.set_expanded(True)

    def add_child(self, node):
        self._children.append(node)

    def index(self, node) -> int:
        for i in range(self.child_count()):
            if self._children[i] == node:
                return i
        return -1

    def get_prev_sibling(self):
        if not self._parent:
            return None
        i = self._parent.index(self)
        n = self._parent.child_count()
        if 0 < i:
            return self._parent.get_child(i - 1)
        return None

    def get_next_sibling(self):
        if not self._parent:
            return None
        i = self._parent.index(self)
        n = self._parent.child_count()
        if 0 <= i < (n - 1):
            return self._parent.get_child(i + 1)
        return None

    def get_path(self, root) -> str:
        parts = []
        cur_node = self
        while cur_node.get_parent() is not None:
            parts.append(cur_node.get_name())
            cur_node = cur_node.get_parent()
        parts = list(reversed(parts))
        return os.path.join(root, *parts)


class DirTreePlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(20, 0))
        self._offset = 0
        self._search_term = ''
        self._node_order = {}
        cfg = config.get_section('dirtree')
        self._root = os.getcwd()
        if 'root' in cfg:
            self._root = cfg['root']
        else:
            cfg['root'] = self._root
        self._tree = TreeNode('', True)
        self.scan(self._tree, self._root, 0)
        self._cur_y = -1
        if self._tree.child_count() > 0:
            self._cur_y = 0

    def scan(self, tree, path: str, indent: int):
        spaces = ' ' * indent
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
        self._render_node(self._tree, 0, -self._offset)

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
        self._cur_y += 1

    def action_move_up(self):
        if self._cur_y > 0:
            self._cur_y -= 1

    def action_enter(self):
        if self._cur_y in self._node_order:
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
        results = self.dfs_search(self._tree, self._search_term)
        results.sort(key=lambda node: node.get_name())
        results.sort(key=lambda node: node.get_path(self._root).count('/'))
        if results:
            res = results[0]
            res.expand_tree()
            for y in sorted(self._node_order.keys()):
                node = self._node_order.get(y)
                if node is res:
                    self._cur_y = y
                    break

    def process_key(self, key: str):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)
        else:
            self.clear_search()

    def on_action(self, action: str):
        self.clear_search()
