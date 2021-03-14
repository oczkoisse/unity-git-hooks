"""This module provides abstractions for Git repositories.

For ordinary Git repositories, a GitRepository class is provided. Unity project
related specifics are abstracted into a UnityGitRepository class.
"""
from pathlib import Path, PurePath
from typing import Tuple, Collection, Mapping
from subprocess import check_output

from .fs.pathtree import PathTree, PathNode


class GitRepository:
    """Represents a Git repository on the file system."""

    def __init__(self, path: str, init=False):
        """Create an abstraction for a Git repository at the given path.

        Args:
            path (str): path to the Git repository root directory
            init (bool, optional): if True, initialize Git at the given path if
            not already initialized. Defaults to False.

        Raises:
            ValueError: if the given path does not exist
        """
        path = Path(path)
        if not path.is_dir():
            raise ValueError("Directory does not exist: {path}")
        self._root = path
        self._git_initd = (path / ".git").is_dir()
        if not self._git_initd and init:
            self.init()

    @property
    def root(self) -> Path:
        """Get the path to the root of this Git repository.

        Returns:
            Path: path to the root of this Git repository
        """
        return self._root

    def init(self):
        """Initialize this Git repository if not already initialized."""
        if not self._git_initd:
            self._run_git("init")

    @property
    def tracked(self) -> Collection[Path]:
        """Get all tracked files.

        The paths of the tracked files are relative to the project root.

        Returns:
            Collection[Path]: paths to the tracked files
        """
        return self.tracked_at(".")

    def tracked_at(self, path: str) -> Collection[Path]:
        """Get tracked files filtered by the given path.

        The paths of the tracked files are relative to the project root.

        Args:
            path (str): path relative to the project root to filter the tracked
            files

        Returns:
            Collection[Path]: paths to the tracked files
        """
        tracked = set()

        # --full-tree means paths are interpreted as relative to root
        cmd = ("ls-tree", "--name-only", "--full-tree", "-r", "HEAD")
        if (self.root / path).is_dir():
            cmd += (path,)

        # List all files as full paths (--full-tree) recursively (-r) in HEAD
        cmd_output = self._run_git(
            *cmd, universal_newlines=True, encoding="utf8"
        ).strip()

        if len(cmd_output) > 0:
            # text mode in check_output normalizes line ending to line feed \n
            for line in cmd_output.split("\n"):
                # Cast to concrete paths native to the OS
                pth = Path(line)
                tracked.add(pth)

        return tracked

    def staged_at(self, path: str) -> Mapping[str, Collection[Tuple[Path]]]:
        """Get staged changes filtered by the given path.

        staged changes as a mapping of change type to the paths affected by the
        change. Change types include 'A' for added paths, 'D' for deleted
        paths and 'R' for renamed paths. Each change type is mapped to a
        collection of path tuples. For change type 'A' and 'D', the tuples
        consist of only one Path. For change type 'R', the tuples consist of
        two Paths, the first being the path being renamed from, and the second
        being the Path being renamed to.

        Returns:
            Mapping[str, Set[Tuple[Path]]]: a mapping of change type to
            affected path(s).
        """
        changes = {}

        # Compare the staging area/index (diff-index --cached) with the
        # previous commit (HEAD) and detect changes that are renames
        # (--find-renames) and list name, change type (--name-status).
        # The output uses NULs as field delimiters (-z)
        cmd = (
            "diff",
            "--cached",
            "--name-status",
            "--find-renames",
            "-z",
        )
        if (self.root / path).is_dir():
            cmd += ("--", path)

        # Command output tends to have trailing NULs so trim those
        cmd_output = (
            self._run_git(*cmd, universal_newlines=True, encoding="utf8")
            .strip()
            .strip("\0")
        )

        if len(cmd_output) > 0:
            words = cmd_output.split("\0")

            i = 0
            while i < len(words):
                change = words[i]
                if change == "A" and i + 1 < len(words):
                    # Detect additions
                    # Cast to concrete paths native to the OS
                    path = Path(words[i + 1])
                    # Paths are immutable and hashable
                    changes.setdefault(change, set()).add((path,))
                    i += 2
                elif change == "D" and i + 1 < len(words):
                    # Detect deletions
                    # Cast to concrete paths native to the OS
                    path = Path(words[i + 1])
                    # Paths are immutable and hashable
                    changes.setdefault(change, set()).add((path,))
                    i += 2
                elif change.startswith("R") and i + 2 < len(words):
                    # Detect renames
                    # Cast to concrete paths native to the OS
                    path_from, path_to = Path(words[i + 1]), Path(words[i + 2])
                    # Putting a tuple of paths inside set is okay because
                    # paths are immutable and hashable
                    # and tuples of hashable elements are hashable
                    changes.setdefault("R", set()).add((path_from, path_to))
                    i += 3
                else:
                    # Go to next word, essential to prevent an infinite loop on
                    # encountering an unaccounted for change type.
                    # Such changes are C (copy), M (modification),
                    # T (file type change), U (unmerged file),
                    # X (unknown change type), etc.
                    i += 1
        return changes

    @property
    def staged(self):
        """Get all staged changes.

        staged changes as a mapping of change type to the paths affected by the
        change. Change types include 'A' for added paths, 'D' for deleted
        paths and 'R' for renamed paths. Each change type is mapped to a
        collection of path tuples. For change type 'A' and 'D', the tuples
        consist of only one Path. For change type 'R', the tuples consist of
        two Paths, the first being the path being renamed from, and the second
        being the Path being renamed to.

        Returns:
            Mapping[str, Set[Tuple[Path]]]: a mapping of change type to
            affected path(s).
        """
        return self.staged_at(".")

    def rename(self, *from_to: str):
        """Rename files and stage the changes.

        Note that each path to rename is specified as a (from, to) pair of
        paths. The paths are interpreted as relative to the repository root.
        """
        if len(from_to) > 0:
            if all([len(p) == 2 and self.is_file(p[0]) for p in from_to]):
                for old, new in from_to:
                    self._run_git("mv", old, new)

    def add(self, *paths: str):
        """Add the given paths and stage the changes.

        The paths are interpreted as relative to the repository root.

        Args:
            paths (str): paths to the files to be added
        """
        if len(paths) > 0:
            if all(self.is_file(p) for p in paths):
                self._run_git("add", *paths)

    def remove(self, *paths: str):
        """Remove given paths and stage the changes.

        The paths are interpreted as relative to the repository root.

        Args:
            paths (str): paths to the files to be deleted
        """
        if len(paths) > 0:
            if all(self.is_file(p) for p in paths):
                self._run_git("rm", *paths)

    def commit(self, message: str):
        """Commit the staged files with the given commit message.

        Args:
            message (str): message for the commit
        """
        self._run_git("commit", "-m", message)

    def is_dir(self, path: str) -> bool:
        """Check if a directory exists at the given path.

        Args:
            path (str): path of the directory

        Returns:
            bool: True if a directory exists at the given path, False otherwise
        """
        return self._abs_path(path).is_dir()

    def is_file(self, path: str) -> bool:
        """Check if a file exists at the given path.

        Args:
            path (str): path of the file

        Returns:
            bool: True if a file exists at the given path, False otherwise
        """
        return self._abs_path(path).is_file()

    def path_exists(self, path: str) -> bool:
        """Check if the given path exists on the file system.

        Args:
            path (str): path relative to the project root

        Returns:
            bool: True if the path exists, False otherwise
        """
        return self._abs_path(path).exists()

    def _run_git(self, *args: str, **kwargs):
        """Invoke Git at the project root with the given arguments.

        The keyword arguments are forwarded to subprocess.check_output.

        Raises:
            CalledProcessError: if the exit code of Git command was non-zero

        Returns:
            bytes: the output of the Git command
        """
        return check_output(("git", "-C", self._root) + args, **kwargs)

    def _abs_path(self, path: str) -> Path:
        """Get the absolute path given a path relative to the project root.

        Args:
            path (str): a path relative to the project root

        Returns:
            Path: an absolute path
        """
        return self._root / path


class UnityGitRepository(GitRepository):
    """Represents a Git repository for a Unity project.

    A UnityGitRepository has a few convenience methods for determining assets,
    metafiles, etc.
    """

    def __init__(self, path: str, init=False):
        """Create an abstraction for a Unity Git project at the given path.

        For a project to be a Unity project, it is assumed to have an Assets/
        directory at the project root.

        Args:
            path (str): path to the Git repository root directory
            init (bool, optional): if True, initialize Git at the given path if
            not already initialized. Defaults to False.

        Raises:
            ValueError: if the given path does not exist
            ValueError: if the given path is not a Unity project
        """
        super().__init__(path, init)

        if not self.is_dir("Assets"):
            # 'Assets/' does not exist
            raise ValueError("Not a Unity git repository")

    @staticmethod
    def is_asset(path: Path) -> bool:
        """Check if the given path is an asset.

        Unity considers anything under 'Assets/' directory to be an asset, be
        it a file or a directory. Each asset has a unique .meta file.
        Importantly, meta files are not assets. Dot-prefixed directories, and
        anything in them, are excluded from being an asset. Note that hte path
        need not exist on the file system for this to return True.

        Args:
            path (Path): path to a file or directory relative to the project
            root

        Returns:
            bool: True if the given path is an asset, False otherwise
        """
        parts = path.parts
        # Asset is whatever Unity gives a .meta file
        if len(parts) > 1 and parts[0] == "Assets":
            # Path must begin with 'Assets/' and have at least one more
            # component. None of the path components can start with a period.
            # A meta file is not an Asset
            return not UnityGitRepository.is_hidden(path) and path.suffix != ".meta"
        else:
            # Anything not under 'Assets/' is not an asset
            return False

    @staticmethod
    def is_hidden(path: PurePath) -> bool:
        """Check if the given path will be considered hidden by Unity.

        Unity considers anything that beings with a dot (.) to be hidden. If it
        is a directory, then anything contained by the directory is also
        hidden. Note that hte path need not exist on the file system for this
        to return True.

        Args:
            path (PurePath): path to check, relative to the project root

        Returns:
            bool: True if the given path is hidden, False otherwise
        """
        return any([p.startswith(".") for p in path.parts])

    @staticmethod
    def is_meta_file(path: PurePath) -> bool:
        """Check if the given path is a Unity .meta file.

        Note that the check is superficially based on the filename only. If the
        .meta suffix is removed from the given path, and the resulting path
        would point to a valid asset, then it is a valid .meta file.

        Args:
            path (PurePath): path to the meta file relative to the project root

        Returns:
            bool: True if the path points to a .meta file, False otherwise
        """
        parts = path.parts
        if len(parts) > 1 and path.parts[0] == "Assets":
            # Path must begin with 'Assets/' and have at least one more
            # component. None of the path components can start with a period
            # Path suffix must be .meta
            return not UnityGitRepository.is_hidden(path) and path.suffix == ".meta"
        else:
            # Anything not under 'Assets/' is not a meta file
            return False

    @staticmethod
    def meta_file_for_asset(asset_path: PurePath) -> PurePath:
        """Appends .meta suffix to an asset path to create a meta file path.

        Args:
            asset_path (Path): asset path to get .meta path for

        Raises:
            ValueError: if asset path is a .meta file

        Returns:
            Path: a path with .meta suffix appended
        """
        # Meta files are not assets
        if asset_path.suffix == ".meta":
            raise ValueError(f"{asset_path} is not an asset")
        else:
            return asset_path.with_suffix(asset_path.suffix + ".meta")

    @staticmethod
    def asset_for_meta_file(meta_file_path: Path):
        """Removes .meta suffix from a meta file path to create an asset path.

        Args:
            meta_file_path (Path): meta file path to get asset path for

        Raises:
            ValueError: if meta file path is not a meta file

        Returns:
            Path: a path with .meta suffix removed
        """
        if meta_file_path.suffix != ".meta":
            raise ValueError(f"{meta_file_path} is not a meta file")
        return meta_file_path.with_suffix("")

    def proposed(self):
        assets = filter(self.is_asset, self.tracked_at("Assets/"))
        tree = PathTree.from_iterable(assets, self.root / "Assets")

        for change, paths in self.staged_at("Assets/").items():
            if change == "D":
                for (path,) in paths:
                    tree.prune(path, PurePath("Assets"))
            elif change == "A":
                for (path,) in paths:
                    tree.add(path)
            elif change == "R":
                for old, new in paths:
                    tree.prune(path, PurePath("Assets"))
                    tree.add(new)
        return tree
