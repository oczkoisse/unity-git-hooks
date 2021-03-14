from pathlib import PurePath

import pytest

from check_unity_meta_files.util.fs.pathtree import PathTree


@pytest.fixture
def tree():
    return PathTree("path/to/some/dir")


@pytest.mark.parametrize(
    "paths,should_be_dirs",
    [[("a", "b"), tuple()], [("a", "b/c"), ("b",)], [("a/b", "c/d", "e"), ("a", "c")]],
)
def test_files_and_dirs_can_be_distinguished(tree, paths, should_be_dirs):
    for path in map(PurePath, paths):
        tree.add(path)

    for f in map(PurePath, paths):
        assert not tree.has_children(f)

    for d in map(PurePath, should_be_dirs):
        assert tree.has_children(d)


@pytest.mark.parametrize(
    "paths,duplicates", [[("a",), ("a",)], [("a", "b/c"), ("b/c",)]]
)
def test_adding_duplicates_doesnt_replace_existing_nodes(tree, paths, duplicates):
    for path in map(PurePath, paths):
        tree.add(path)

    existing_nodes = []
    for duplicate in map(PurePath, duplicates):
        existing_nodes.append(tree.descendant(duplicate))

    for duplicate in map(PurePath, duplicates):
        tree.add(duplicate)

    new_nodes = []
    for duplicate in map(PurePath, duplicates):
        new_nodes.append(tree.descendant(duplicate))

    for e_node, n_node in zip(existing_nodes, new_nodes):
        assert e_node is n_node


@pytest.mark.parametrize("paths", [("a", "b"), ("a/b", "c/d"), ("a/b", "c")])
def test_tree_has_added_paths(tree, paths):
    for path in map(PurePath, paths):
        tree.add(path)

    for path in map(PurePath, paths):
        assert tree.has_descendant(path)


@pytest.mark.parametrize(
    "paths,removed", [[("a/b", "c"), ("c",)], [("a/b", "c"), ("a/b",)]]
)
def test_tree_doesnt_have_removed_paths(tree, paths, removed):
    for path in map(PurePath, paths):
        tree.add(path)

    for path in map(PurePath, removed):
        tree.remove(path)
        assert not tree.has_descendant(path)


@pytest.mark.parametrize(
    "paths,removed", [[("a/b", "a/c"), "a"], [("a/b/c", "a/b/d"), "a/b"]]
)
def test_removing_a_directory_removes_its_children(tree, paths, removed):
    for path in map(PurePath, paths):
        tree.add(path)

    removed_dir = PurePath(removed)
    children = tree.children(removed_dir)
    tree.remove(removed_dir)

    for child in children:
        assert not tree.has_descendant(removed_dir / child.name)


@pytest.mark.parametrize("paths", [("a",), ("a/b", "a/c", "d")])
def test_removing_at_root_clears_the_tree(tree, paths):
    for path in map(PurePath, paths):
        tree.add(path)

    anchor = PurePath(".")
    tree.remove(anchor)
    assert len(tree.children(anchor)) == 0


@pytest.mark.parametrize(
    "paths,expected",
    [
        [("a",), [".", "a"]],
        [("a/b", "a/c"), [".", "a", "b", "c"]],
        [("a/b/c", "a/b/d", "a/e/f"), [".", "a", "b", "e", "c", "d", "f"]],
    ],
)
def test_breadth_first_traversal(tree, paths, expected):
    for path in map(PurePath, paths):
        tree.add(path)

    traversed = []
    for node in tree.traverse_breadth_first():
        traversed.append(node.name)

    assert traversed == expected


@pytest.mark.parametrize(
    "paths,expected",
    [
        [("a",), [".", "a"]],
        [("a/b", "a/c"), [".", "a", "c", "b"]],
        [("a/b/c", "a/b/d", "a/e/f"), [".", "a", "e", "f", "b", "d", "c"]],
    ],
)
def test_depth_first_traversal(tree, paths, expected):
    for path in map(PurePath, paths):
        tree.add(path)

    traversed = []
    for node in tree.traverse_depth_first():
        traversed.append(node.name)

    assert traversed == expected


@pytest.mark.parametrize(
    "paths,expected",
    [
        [("a",), [".", "a"]],
        [("a/b", "a/c"), [".", "a", "a/b", "a/c"]],
        [
            ("a/b/c", "a/b/d", "a/e/f"),
            [".", "a", "a/b", "a/e", "a/b/c", "a/b/d", "a/e/f"],
        ],
    ],
)
def test_all_paths(tree, paths, expected):
    for path in map(PurePath, paths):
        tree.add(path)

    all_paths = list(tree.all_paths())
    assert all_paths == list(map(PurePath, expected))
