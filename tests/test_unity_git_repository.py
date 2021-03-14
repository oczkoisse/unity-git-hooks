from pathlib import Path

import pytest

from check_unity_meta_files.util.git import UnityGitRepository
from check_unity_meta_files.util.fs.file import empty_file


@pytest.fixture
def empty_unity_git_repository(tmp_path) -> UnityGitRepository:
    (tmp_path / "Assets").mkdir()
    return UnityGitRepository(tmp_path, init=True)


@pytest.mark.parametrize("path", ["Assets/file", "Assets/dir/file"])
def test_assets(empty_unity_git_repository, path):
    empty_file(empty_unity_git_repository.root / path)
    assert empty_unity_git_repository.is_asset(Path(path))


@pytest.mark.parametrize(
    "path",
    [
        "file",
        "Assets/.file",
        "Assets/dir/.hidden",
        "Assets/.hiddendir/file",
        "Assets/file.meta",
    ],
)
def test_non_assets(empty_unity_git_repository, path):
    empty_file(empty_unity_git_repository.root / path)
    assert not empty_unity_git_repository.is_asset(Path("Assets"))
    assert not empty_unity_git_repository.is_asset(Path(path))


@pytest.mark.parametrize(
    "path", [".file", ".dir/file", "dir/.hiddendir/file", "dir/.hiddendir/.file"]
)
def test_hidden_file(path):
    assert UnityGitRepository.is_hidden(Path(path))


@pytest.mark.parametrize("path", ["Assets/file.meta", "Assets/dir/file.meta"])
def test_is_meta_file(empty_unity_git_repository, path):
    empty_file(empty_unity_git_repository.root / path)
    assert empty_unity_git_repository.is_meta_file(Path(path))


@pytest.mark.parametrize(
    "path",
    ["file", "file.meta", "Assets/file", "Assets/dir/file", "Assets/.dir/file.meta"],
)
def test_is_not_meta_file(empty_unity_git_repository, path):
    empty_file(empty_unity_git_repository.root / path)
    assert not empty_unity_git_repository.is_meta_file(Path(path))


@pytest.mark.parametrize(
    "path,expected", [["file", "file.meta"], ["dir/file", "dir/file.meta"]]
)
def test_meta_file_for_asset(path, expected):
    assert UnityGitRepository.meta_file_for_asset(Path(path)) == Path(expected)


@pytest.mark.parametrize(
    "path,expected", [["file.meta", "file"], ["dir/file.meta", "dir/file"]]
)
def test_asset_for_meta_file(path, expected):
    assert UnityGitRepository.asset_for_meta_file(Path(path)) == Path(expected)


@pytest.mark.parametrize(
    "paths_to_add,paths_to_remove,expected_removed,expected_remaining",
    [
        (["Assets/a/b"], ["Assets/a/b"], ["Assets/a/b", "Assets/a"], ["Assets"]),
        (
            ["Assets/a/b", "Assets/a/c"],
            ["Assets/a/b"],
            ["Assets/a/b"],
            ["Assets", "Assets/a", "Assets/a/c"],
        ),
        (
            ["Assets/a/b/c", "Assets/a/e"],
            ["Assets/a/b/c"],
            ["Assets/a/b/c", "Assets/a/b"],
            ["Assets", "Assets/a", "Assets/a/e"],
        ),
    ],
)
def test_proposed_removes_empty_parents(
    empty_unity_git_repository,
    paths_to_add,
    paths_to_remove,
    expected_removed,
    expected_remaining,
):
    for path in map(Path, paths_to_add):
        empty_file(empty_unity_git_repository.root / path)
        empty_unity_git_repository.add(path)

    empty_unity_git_repository.commit("Initial commit")

    for path in map(Path, paths_to_remove):
        empty_unity_git_repository.remove(path)

    proposed = empty_unity_git_repository.proposed()

    for path in map(Path, expected_removed):
        assert not proposed.has_descendant(path)

    for path in map(Path, expected_remaining):
        assert proposed.has_descendant(path)


@pytest.mark.parametrize(
    "paths_to_add,new_added_paths", [(["Assets/a"], ["Assets/b", "Assets/c"])]
)
def test_proposed_has_newly_added_assets(
    empty_unity_git_repository, paths_to_add, new_added_paths
):
    for path in map(Path, paths_to_add):
        empty_file(empty_unity_git_repository.root / path)

    empty_unity_git_repository.add(*paths_to_add)

    empty_unity_git_repository.commit("Initial commit")

    for path in map(Path, new_added_paths):
        empty_file(empty_unity_git_repository.root / path)

    empty_unity_git_repository.add(*new_added_paths)

    proposed = empty_unity_git_repository.proposed()

    for path in map(Path, new_added_paths):
        assert proposed.has_descendant(path)


@pytest.mark.parametrize(
    "paths_to_add,paths_to_remove", [(["Assets/a", "Assets/b"], ["Assets/b"])]
)
def test_proposed_doesnt_have_removed_assets(
    empty_unity_git_repository, paths_to_add, paths_to_remove
):
    for path in map(Path, paths_to_add):
        empty_file(empty_unity_git_repository.root / path)

    empty_unity_git_repository.add(*paths_to_add)

    empty_unity_git_repository.commit("initial commit")

    empty_unity_git_repository.remove(*paths_to_remove)

    proposed = empty_unity_git_repository.proposed()

    for path in map(Path, paths_to_remove):
        assert not proposed.has_descendant(path)


def test_proposed_renames_assets_that_are_renamed():
    pass
