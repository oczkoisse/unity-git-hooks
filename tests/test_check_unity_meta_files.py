from pathlib import Path, PurePath

import pytest

from typing import Tuple, Iterable

from check_unity_meta_files.check_unity_meta_files import check_unity_meta_files
from check_unity_meta_files.util.git import GitRepository, UnityGitRepository
from check_unity_meta_files.util.fs.file import empty_file


@pytest.fixture
def empty_unity_git_repository(tmp_path) -> UnityGitRepository:
    (tmp_path / "Assets").mkdir()
    return UnityGitRepository(tmp_path, init=True)


def prepare_repo(
    repository: GitRepository, tracked: Iterable[PurePath], staged: Iterable[Tuple]
):
    for path in map(Path, tracked):
        empty_file(repository.root / path)
        repository.add(path)

    repository.commit("initial commit")

    for change in staged:
        change_type = change[0]
        if change_type == "A":
            for path in change[1:]:
                empty_file(repository.root / path)
            repository.add(*change[1:])
        elif change_type == "D":
            repository.remove(*change[1:])
        elif change_type == "R":
            repository.rename(*change[1:])
        else:
            raise NotImplementedError(f"Change {change_type} not implemented")


def both(path: str):
    asset_path = asset(path)
    return asset_path, UnityGitRepository.meta_file_for_asset(asset_path)


def asset(path: str):
    return PurePath("Assets") / path


def meta(path: str):
    return UnityGitRepository.meta_file_for_asset(asset(path))


@pytest.mark.parametrize(
    "tracked,staged,missing,orphans",
    [
        # Everything okay
        ([*both("a")], [], [], []),
        (
            [*both("a"), *both("dir/b"), meta("dir")],
            [],
            [],
            [],
        ),
        # Missing .meta files
        ([asset("a")], [], [meta("a")], []),
        (
            [asset("dir/a"), *both("dir/b"), meta("dir")],
            [],
            [meta("dir/a")],
            [],
        ),
        (
            [*both("a"), *both("dir/b")],
            [],
            [meta("dir")],
            [],
        ),
        # Orphan .meta files
        ([meta("a")], [], [], [meta("a")]),
        (
            [meta("dir/a"), *both("b"), meta("dir")],
            [],
            [],
            [meta("dir/a")],
        ),
        # Adding asset without adding .meta file
        ([*both("a")], [("A", asset("b"))], [meta("b")], []),
        # Adding .meta file without adding asset
        (
            [*both("a")],
            [("A", meta("b"))],
            [],
            [meta("b")],
        ),
        # Removing asset without removing .meta file
        ([*both("a")], [("D", asset("a"))], [], [meta("a")]),
        # Removing .meta file without removing asset
        (
            [*both("a")],
            [("D", meta("a"))],
            [meta("a")],
            [],
        ),
    ],
)
def test_check_unity_meta_files(
    empty_unity_git_repository, tracked, staged, missing, orphans
):
    prepare_repo(empty_unity_git_repository, tracked, staged)

    result = check_unity_meta_files(empty_unity_git_repository)
    _, got_missing, got_orphans = result
    assert set(missing) == got_missing
    assert set(orphans) == got_orphans
