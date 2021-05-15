import os


class TreeNode:
    def __init__(self, name: str, is_dir: bool, parent):
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
        if 0 < i < n:
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


def convert_node(node: TreeNode, subtree: dict):
    for name in sorted(subtree.keys()):
        value = subtree.get(name)
        if isinstance(value, dict):
            child = TreeNode(name, True, node)
            node.add_child(child)
            convert_node(child, value)
        else:
            child = TreeNode(name, False, node)
            node.add_child(child)


def convert_tree(tree):
    node = TreeNode('', True, None)
    convert_node(node, tree)
    return node
