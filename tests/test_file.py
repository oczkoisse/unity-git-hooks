import pytest

from check_unity_meta_files.util.fs.file import open_file


def test_open_file_overwrites_existing_file_by_default(tmp_path):
    f = open(tmp_path / "a.txt", "w")
    f.write("hello")
    f.close()

    with open_file(tmp_path / "a.txt") as f:
        pass

    f = open(tmp_path / "a.txt", "r")
    content = f.read()
    f.close()

    assert content == ""


def test_open_file_closes_on_exiting_context(tmp_path):
    with open_file(tmp_path / "a.txt") as f:
        f.write("hello")

    with pytest.raises(ValueError):
        f.write("world")
