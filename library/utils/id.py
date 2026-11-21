import re
from typing import Optional, Tuple

# A resource id is the id of a file (`path_to_name` of its path: `__` escaped as `_%5F`, `:` as `---DRIVE`), and for a
# resource in the file `__` and its path in the file's data (`children/3/item/data`). That path never contains `__`
# and never starts with `_`, so the last `__` of an id separates the two, also after a file name ending in `_`
# (`TRACK___children/0` = `children/0` of `TRACK_`)
ID_SEPARATOR = '__'


def path_to_name(path: str) -> str:
    """The id of the file at `path`"""
    return path.replace('\\', '/').replace(':', '---DRIVE').replace(ID_SEPARATOR, '_%5F')


def split_id(id: str) -> Tuple[str, str]:
    """(file id, path in the file's data) of a resource id, the path '' for the id of a file"""
    file_id, separator, path = id.rpartition(ID_SEPARATOR)
    return (file_id, path) if separator else (id, '')


def is_file_id(id: str) -> bool:
    """Whether a resource id is the id of a file (the file's data), not of a resource in it"""
    return ID_SEPARATOR not in id


def id_to_path(id: str) -> str:
    """The path of the file holding a resource"""
    return split_id(id)[0].replace('_%5F', ID_SEPARATOR).replace('---DRIVE', ':')


def join_id(base_id: str, *suffix_ids):
    res = base_id
    for i, suff in enumerate(suffix_ids):
        if i > 0 or not is_file_id(base_id):
            res += '/' + suff
        else:
            res += ID_SEPARATOR + suff
    return res


def parse_item_id(id: Optional[str]) -> Optional[Tuple[str, int]]:
    """(archive id, index in its `children`) of the id of an archive item's data (`<archive>__children/<i>/item/data`,
    `.../children/<i>/item/data` in a nested archive), None for another id"""
    match = re.fullmatch(r'(.*)(?:__|/)children/(\d+)/item/data', id or '')
    return (match.group(1), int(match.group(2))) if match else None


def split_last_id_part(id: str) -> Tuple[str, str]:
    """(parent id, last key) of a resource id; (directory, file name) for the id of a file"""
    file_id, path = split_id(id)
    if not path:
        parent, _, key = id.rpartition('/')
        return parent, key
    parent_path, _, key = path.rpartition('/')
    return (join_id(file_id, parent_path) if parent_path else file_id), key
