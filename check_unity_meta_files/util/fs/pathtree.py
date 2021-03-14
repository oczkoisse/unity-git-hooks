"""This module consists of PathNode and PathTree.

PathNode and PathTree together provide an abstraction of paths organized in a
tree structure.
"""
from pathlib import PurePath
from collections import deque, OrderedDict
from typing import Sequence, Iterable, Union


class PathNode:
    r"""This class represents a node that is a part of PathTree.

    A PathNode has a name and zero or more children PathNodes. The name of the
    PathNode should be a valid Path part (for example, it shouldn't contain /
    or \). This is necessary so that a descendant node can be referred to by a
    PurePath in PathTree.
    """

    def __init__(self, name: str, parent: "PathNode"):
        """Create a PathNode with the given name and parent.

        If the parent node is None, the node is considered to be a root node.

        Args:
            name (str): name of the node to be created
            parent (PathNode): parent node. If None, the node is considered to
            be a root node.

        Raises:
            ValueError: if the name is empty string
        """
        if len(name) == 0:
            raise ValueError("File node name cannot be ''")
        self._name = name
        self._parent = parent
        # Mapping of childname to FileNode
        self._children = OrderedDict()

    @property
    def name(self) -> str:
        """Get the name of the path node.

        Returns:
            str: name of the path node
        """
        return self._name

    def has_children(self) -> bool:
        """Check whether the path node has any children.

        Returns:
            bool: True if the path node has at least one child, False otherwise
        """
        return self.children_count > 0

    def add_child(self, childname: str) -> "PathNode":
        """Add a child with the given name to this node.

        Raises:
            ValueError: If the child name consists of multiple levels like a/b
            ValueError: If a child of the same name as the one being added
            already exists

        Returns:
            PathNode: the node for the child just added
        """
        if len(PurePath(childname).parts) > 1:
            raise ValueError(f"Added child with multiple levels: {childname}")
        if childname in self._children:
            raise ValueError(f"Duplicate child added: {childname}")

        child = PathNode(childname, self)
        self._children[childname] = child
        return child

    def remove_child(self, childname: str) -> "PathNode":
        """Remove a child with the given name from this node.

        Raises:
            ValueError: If a child of the name as the one being removed doesn't
            exist

        Returns:
            PathNode: parent node of the child just removed i.e. itself
        """
        if childname not in self._children:
            raise ValueError(f"Removed non-existent child: {childname}")

        self._children.pop(childname)
        return self

    def has_child(self, childname: str) -> bool:
        """Check whether the node has any child with the given name.

        Args:
            childname (str): name of the child node

        Returns:
            bool: True if the node has a child of the given name, False
            otherwise
        """
        return childname in self._children

    def has_descendant(self, path: PurePath) -> bool:
        """Check whether the node has a descendant with the given path.

        The path is composed such that each part is a child name. The path is
        interpreted relative to the current node.

        Args:
            path (PurePath): path to the descendant relative to this node

        Returns:
            bool: True if the node has a descendant with the given path, False
            otherwise
        """
        node = self
        for part in path.parts:
            if node.has_child(part):
                node = node.child(part)
            else:
                return False
        return True

    def child(self, childname: str) -> "PathNode":
        """Get the node for the child with the given name.

        Raises:
            ValueError: if a child with the given name doesn't exist

        Returns:
            PathNode: a node with the given name if it exists, None otherwise
        """
        if childname not in self._children:
            raise ValueError(f"'{self.name}' has no child named '{childname}'")
        return self._children[childname]

    def descendant(self, path: PurePath) -> Union["PathNode", None]:
        """Get the node for the descendant with the given name.

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            PathNode: a node at the given path relative to this node
        """
        node = self
        for part in path.parts:
            if node.has_child(part):
                node = node.child(part)
            else:
                raise ValueError("fCannot remove non-existent path: {path}")
        return node

    def __str__(self) -> str:
        """Get a print friendly string representation of the current node.

        The output is similar to what one would get with a tree command.
        Briefly, the name of the node is on its own line, followed by └─
        prefixed names of its children, each on a separate line. For example:
            name
            └─ child1
            └─ child2

        Returns:
            str: a string representation of the current node
        """
        names = [self._name]
        names.extend(map(lambda x: f"└─ {x}", self._children.keys()))
        return "\n".join(names)

    def __repr__(self) -> str:
        """Get a string representation of the current node.

        The string is formatted as a pair: ('name', ['child1', 'child2', ...]).
        The first element is the name of this node. The second element is a
        list of names of all the children of this node.

        Returns:
            str: a string representation of the current node
        """
        children = ["'{k}'" for k in self._children.keys()]
        return f"('{self._name}'', [{', '.join(children)}])"

    @property
    def children(self) -> Sequence["PathNode"]:
        """Get all the nodes that are children of this node.

        Returns:
            Sequence[PathNode]: all the nodes that are child of this node
        """
        return [self._children[childname] for childname in self._children]

    @property
    def children_count(self) -> int:
        """Get the number of children that this node has.

        Returns:
            int: total number of nodes that are a child of this node
        """
        return len(self._children)

    def is_root_node(self) -> bool:
        """Check whether this node is a root node.

        A node is considered a root node if its parent is None.

        Returns:
            bool: True if this node is a root node, False otherwise
        """
        return self._parent is None

    def is_child_of(self, node: "PathNode") -> bool:
        """Check if this node is a child of the given node.

        Args:
            node (PathNode): the node to be checked for parent relationship

        Returns:
            bool: True if the given node is a parent of this node, False
            otherwise
        """
        return self.parent is node

    def is_parent_of(self, node: "PathNode") -> bool:
        """Check if this node is the parent of the given node.

        Args:
            node (PathNode): the node to be checked for child relationship

        Returns:
            bool: True if the given node is a child of this node, False
            otherwise
        """
        return node.parent is self

    @property
    def parent(self) -> Union["PathNode", None]:
        """Get the parent of this node.

        Returns:
            Union[PathNode, None]: the parent node, possibly None if this is a
            root node
        """
        return self._parent

    def clear(self):
        """Remove all the descendents of this node.

        Note that if a reference to any descendant node exists after clearing,
        that descendant node may have an (invalid) reference to a parent that
        may not exist. Only clear a node if you're never going to use any of
        its descendent nodes.
        """
        self._children.clear()


class PathTree:
    """A PathTree consists of PathNodes organized as a tree.

    Although PathNodes can form a tree implicitly via parent linkages, PathTree
    provides convenient methods to perform PathNode operations using a path
    relative to the root node like accessing a descendant for example.
    """

    def __init__(self, path: str):
        """Create a new PathTree with the root path set to the given path.

        Also, an implicit root node with name '.' is created.

        Args:
            path (str): path which the root node name '.' refers to
        """
        self._rootpath = PurePath(path)
        self._root = PathNode(".", None)

    @property
    def rootpath(self) -> PurePath:
        """Get the path which the root node name '.' refers to.

        Returns:
            PurePath: path which the root node name '.' refers to
        """
        return self._rootpath

    def add(self, path: PurePath) -> PathNode:
        """Add a node at the given path.

        The path is interpreted relative to the tree root. Any non-existent
        child nodes are automatically created. If a node already exists for the
        given path, the same is returned.

        Args:
            path (PurePath): path to add to the tree

        Returns:
            PathNode: the node that corresponds to last part of the added path
        """
        self._check_path(path)
        node = self._root
        for part in path.parts:
            if node.has_child(part):
                node = node.child(part)
            else:
                node = node.add_child(part)
        return node

    def remove(self, path: PurePath) -> Union[None, PathNode]:
        """Remove the node at the given path.

        The path is interpreted relative to the tree root. If the node at the
        given path exists, it is removed and its parent node is returned. For a
        root node, the parent is None.

        Args:
            path (PurePath): path to the node to be removed

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            Union[None, PathNode]: parent of the removed node
        """
        if self.is_path_to_root(path):
            self.clear()
            return None
        else:
            parent = self._root.descendant(path.parent)
            parent.remove_child(path.name)
            return parent

    def clear(self):
        """Clear all the nodes in the tree."""
        self._root.clear()

    def is_path_to_root(self, path: PurePath) -> bool:
        """Check whether the given path refers to the root node.

        Args:
            path (PurePath): path to be resolved

        Returns:
            bool: True if the path resolves to root node, False otherwise
        """
        return len(path.parts) == 0

    def children(self, path: PurePath) -> Sequence[PathNode]:
        """Get the children nodes of the node at the given path.

        Args:
            path (PurePath): path to the parent node

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            Sequence[PathNode]: nodes that are children of the node at the
            given path
        """
        node = self.descendant(path)
        return node.children

    def children_count(self, path: PurePath) -> int:
        """Get the number of children that the node at the given path has.

        Args:
            path (PurePath): path of the parent node

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            int: number of children that the node has
        """
        self._check_path(path)
        node = self._root.descendant(path)
        return node.children_count

    def has_children(self, path: PurePath) -> bool:
        """Check whether the node at the given path has any children.

        Args:
            path (PurePath): path of the parent node

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            bool: True if the node at the given path has children, False
            otherwise
        """
        return self.children_count(path) > 0

    def descendant(self, path: PurePath) -> PathNode:
        """Get the descendant node at the given path.

        Args:
            path (PurePath): path to the descendant node

        Raises:
            ValueError: if the given path doesn't exist

        Returns:
            PathNode: the node at the given path, or None if it doesn't exist
        """
        return self._root.descendant(path)

    def has_descendant(self, path: PurePath) -> bool:
        """Check whether the tree has a descendant at the given path.

        Args:
            path (PurePath): path to the descendent node

        Returns:
            bool: True if the tree has a descendant at the given path, False
            otherwise
        """
        return self._root.has_descendant(path)

    def _check_path(self, path: PurePath):
        """Check if the given path is acceptable.

        In particular, only relative paths are allowed.

        Args:
            path (PurePath): path to be checked

        Raises:
            ValueError: if the path is not acceptable
        """
        if path.is_absolute():
            raise ValueError(f"{path} is not a relative path")

    def traverse_breadth_first(self) -> Iterable[PathNode]:
        """Traverse tree nodes in breadth-first form.

        The root node (with name '.') is always returned first, followed by all
        its children in insertion order, followed by all children of its first
        child, then all children of its second child, and so on.

        Returns:
            Iterable[PathNode]: an iterable of tree nodes
        """
        q = deque()
        q.append(self._root)

        while len(q) > 0:
            node = q.popleft()
            yield node

            if node.children_count > 0:
                for child in node.children:
                    q.append(child)

    def traverse_depth_first(self) -> Iterable[PurePath]:
        """Traverse tree nodes in depth-first form.

        The root node (with name '.') is always returned first, followed by its
        firs child in insertion order, followed by its first grandchild in
        insertion order, and so on.

        Returns:
            Iterable[PathNode]: an iterable of tree nodes
        """
        s = []
        s.append(self._root)

        while len(s) > 0:
            node = s.pop()
            yield node
            if node.children_count > 0:
                for child in node.children:
                    s.append(child)

    def all_paths(self) -> Iterable[PurePath]:
        """Generate all possible paths in the given tree.

        Note that this includes non-leaf nodes as well.

        Returns:
            Iterable[PurePath]: an iterable of paths
        """
        q = deque()
        q.append((PurePath("."), [self._root]))

        while len(q) > 0:
            base, nodes = q.popleft()
            for node in nodes:
                path = base / node.name
                yield path
                if node.has_children:
                    q.append((path, node.children))

    @staticmethod
    def from_iterable(paths: Iterable[PurePath], rootpath: PurePath) -> "PathTree":
        """Create a PathTree by adding paths from an iterable of paths.

        Args:
            paths (Iterable[PurePath]): iterable of paths to add
            rootpath (PurePath): path to the root of the tree

        Returns:
            PathTree: tree formed by adding the given paths
        """
        tree = PathTree(rootpath)

        for path in paths:
            tree.add(path)

        return tree

    def prune(self, path: PurePath, limit_path: PurePath):
        """Prune the given path off ancestors that have no children.

        The operation involves removing the node at the given path. If the
        removal leaves its parent childless, the parent is also removed. This
        is repeated recursively until the node at limit_path is reached, at
        which point the pruning is stopped.

        Args:
            path (PurePath): path whose ancestors are to be pruned
            limit_path (PurePath): path at which pruning is stopped

        Raises:
            ValueError: if either of the given path is not acceptable
            ValueError: if either of the given path doesn't exist

        Returns:
            PathNode: parent of the last removed node
        """
        node = self.descendant(path)
        limit_node = self.descendant(limit_path)

        # Hackish way of figuring out if limit_path is a subpath of path
        # Python 3.9 has path.is_relative_to method
        cur_node = node
        while cur_node.parent not in [None, limit_node]:
            cur_node = cur_node.parent

        if cur_node.parent is None:
            raise ValueError(f"Limit {limit_path} must be a subpath of {path}")

        # limit_path is a subpath of path
        parent = node.parent
        parent.remove_child(node.name)

        while (
            not parent.is_root_node()
            and parent is not limit_node
            and not parent.has_children()
        ):
            childname = parent.name
            parent = parent.parent
            parent.remove_child(childname)

        return parent
