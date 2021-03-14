from pathlib import Path

import pytest

from check_unity_meta_files.util.git import GitRepository
from check_unity_meta_files.util.fs.file import empty_file


@pytest.fixture
def empty_git_repository(tmp_path) -> GitRepository:
    return GitRepository(tmp_path, init=True)


def test_git_repository_refuses_invalid_root_path(tmp_path):
    with pytest.raises(ValueError):
        GitRepository(tmp_path / "a")


@pytest.mark.parametrize(
    "added",
    [
        ("file1", "file2"),
        ("dir1/file1", "dir1/file2"),
        ("dir1/file1", "file2"),
        ("dir1/file1", "dir1/file2", "file3"),
    ],
)
def test_tracked_files_equals_committed_files(empty_git_repository, added):
    for path in added:
        empty_file(empty_git_repository.root / path)
    empty_git_repository.add(*added)
    empty_git_repository.commit("Initial commit")
    assert len(added) == len(empty_git_repository.tracked)


@pytest.mark.parametrize(
    "paths_to_add,subdirectory,subdirectory_paths",
    [
        [("file1", "file2"), ".", ("file1", "file2")],
        [("dir1/file1", "dir1/file2"), "dir1", ("dir1/file1", "dir1/file2")],
        [("dir1/file1", "file2"), "dir1", ("dir1/file1",)],
        [("dir1/file1", "dir1/file2", "file3"), "dir1", ("dir1/file1", "dir1/file2")],
    ],
)
def test_tracked_at_only_returns_files_under_subdirectory(
    empty_git_repository, paths_to_add, subdirectory, subdirectory_paths
):
    for path in paths_to_add:
        empty_file(empty_git_repository.root / path)

    empty_git_repository.add(*paths_to_add)
    empty_git_repository.commit("Initial commit")

    tracked = empty_git_repository.tracked_at(subdirectory)
    assert tracked == set(map(Path, subdirectory_paths))


@pytest.mark.parametrize(
    "added",
    [
        ("file1", "file2"),
        ("dir1/file1", "dir1/file2"),
        ("dir1/file1", "file2"),
        ("dir1/file1", "dir1/file2", "file3"),
    ],
)
def test_index_additions_equals_added_files(empty_git_repository, added):
    for path in added:
        empty_file(empty_git_repository.root / path)
    empty_git_repository.add(*added)
    add_changes = empty_git_repository.staged["A"]
    assert len(added) == len(add_changes)


@pytest.mark.parametrize(
    "paths_to_add,paths_to_delete",
    [
        (("file1", "file2"), ("file1",)),
        (("dir1/file1", "dir1/file2"), ("dir1/file2",)),
        (("dir1/file1", "dir1/file2", "file3"), ("file3", "dir1/file1")),
    ],
)
def test_index_deletions_equals_deleted_files(
    empty_git_repository, paths_to_add, paths_to_delete
):
    for path in paths_to_add:
        empty_file(empty_git_repository.root / path)
    empty_git_repository.add(*paths_to_add)
    empty_git_repository.commit("Initial commit")
    empty_git_repository.remove(*paths_to_delete)
    delete_changes = empty_git_repository.staged["D"]
    assert len(paths_to_delete) == len(delete_changes)


@pytest.mark.parametrize(
    "paths_to_add,paths_to_rename",
    [
        (("file1", "file2"), (("file1", "file3"),)),
        (("dir1/file1", "dir1/file2"), (("dir1/file2", "dir1/file3"),)),
    ],
)
def test_index_renames_equals_renamed_files(
    empty_git_repository, paths_to_add, paths_to_rename
):
    for path in paths_to_add:
        empty_file(empty_git_repository.root / path)
    empty_git_repository.add(*paths_to_add)
    empty_git_repository.commit("Initial commit")
    empty_git_repository.rename(*paths_to_rename)
    rename_changes = empty_git_repository.staged["R"]
    assert len(paths_to_rename) == len(rename_changes)
