from pathlib import PurePath
import os
import sys

from .util.git import UnityGitRepository
from .util.fs.pathtree import PathTree


def check_unity_meta_files(repository: UnityGitRepository) -> bool:
    missing = set()
    orphans = set()

    # Get tracked files under Assets that are not hidden
    tracked = filter(
        lambda p: not repository.is_hidden(p), repository.tracked_at("Assets/")
    )

    # Convert to a PathTree
    tracked_tree = PathTree.from_iterable(tracked, repository.root)

    # Go through staged items in 'Assets' directory
    for change, paths in repository.staged_at("Assets/").items():
        if change == "D":
            for (path,) in paths:
                # Hidden files should be ignored
                if not UnityGitRepository.is_hidden(path):
                    # Prune but not beyond Assets directory
                    tracked_tree.prune(path, PurePath("Assets"))
        elif change == "A":
            for (path,) in paths:
                # Hidden files should be ignored
                if not UnityGitRepository.is_hidden(path):
                    tracked_tree.add(path)
        elif change == "R":
            for old, new in paths:
                # Hidden files should be ignored
                if not UnityGitRepository.is_hidden(old):
                    # Prune but not beyond Assets directory
                    tracked_tree.prune(old, PurePath("Assets"))
                # Hidden files should be ignored
                if not UnityGitRepository.is_hidden(new):
                    tracked_tree.add(new)

    for path in tracked_tree.all_paths():
        if repository.is_asset(path) and repository.path_exists(path):
            meta_file_path = UnityGitRepository.meta_file_for_asset(path)
            if not repository.is_file(meta_file_path):
                missing.add(meta_file_path)
        elif repository.is_meta_file(path) and repository.is_file(path):
            asset_path = UnityGitRepository.asset_for_meta_file(path)
            if not repository.path_exists(asset_path):
                orphans.add(path)

    return len(missing) + len(orphans) == 0, missing, orphans


def main():
    repository = UnityGitRepository(os.getcwd())
    success, missing, orphans = check_unity_meta_files(repository)

    for path in missing:
        print(f"Missing .meta file: {path}")

    for path in orphans:
        print(f"Orphan .meta file: {path}")

    return 0 if success else 1


if __file__ == "__main__":
    sys.exit(main())
