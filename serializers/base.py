import os
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config import conversion_config
from library.utils import format_exception, path_join
from library.utils.id import join_id


@dataclass(frozen=True)
class UiSerialization:
    """What the GUI's convert panel offers for the blocks of a serializer (`ResourceSerializer.ui`): `file_type` (the
    label of the output), `is_directory`, `suffix` (of the output file name), `reversible` (the output imports back),
    `settings_patch` (the conversion settings of an export made for an import), `import_guide` (the guide the GUI
    shows before an import)"""

    file_type: Optional[str]
    is_directory: bool = False
    suffix: Optional[str] = None
    reversible: bool = False
    settings_patch: Dict = field(default_factory=dict)
    import_guide: Optional[str] = None

    def as_dict(self) -> dict:
        res = {
            'file_type': self.file_type,
            'is_directory': self.is_directory,
            'output_file_name_suffix': self.suffix,
            'reversible': self.reversible,
            'reversible_settings_patch': dict(self.settings_patch),
        }
        if self.import_guide is not None:
            res['import_guide'] = self.import_guide
        return res


JSON_UI = UiSerialization('json', suffix='.json')
REVERSIBLE_JSON_UI = UiSerialization('json', suffix='.json', reversible=True)
PNG_UI = UiSerialization('png', suffix='.png')
REVERSIBLE_PNG_UI = UiSerialization('png', suffix='.png', reversible=True)
DIRECTORY_UI = UiSerialization('directory', is_directory=True)


class ResourceSerializer(ABC):
    settings = conversion_config()
    # the GUI's convert panel for the blocks of the serializer, None: not convertible from the GUI
    ui: Optional[UiSerialization] = None

    def patch_settings(self, settings_patch: dict):
        self.settings.update(settings_patch)

    def ui_serialization(self) -> Optional[dict]:
        return self.ui.as_dict() if self.ui is not None else None

    @abstractmethod
    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        raise NotImplementedError

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        raise NotImplementedError


class DelegateBlockSerializer(ResourceSerializer):
    def is_dir(self, block, data):
        from serializers import get_serializer

        sub_block, sub_data = block.possible_blocks[data['choice_index']], data['data']
        serializer = get_serializer(sub_block, sub_data)
        return serializer.is_dir

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        from serializers import get_serializer

        sub_block, sub_data = block.possible_blocks[data['choice_index']], data['data']
        serializer = get_serializer(sub_block, sub_data)
        return serializer.serialize(sub_data, path=path, id=join_id(id, 'data'), block=sub_block)


def current_resource(id: Optional[str], block=None) -> Optional[dict]:
    """The data loaded under `id`, which an import replaces: None without an id or loaded data, for data which is no
    dict, and (with `block`) for the data of another block class"""
    if not id:
        return None
    from library import require_resource

    try:
        (_, current_block, current), _ = require_resource(id)
    except Exception:
        return None
    if not isinstance(current, dict) or (block is not None and type(current_block) is not type(block)):
        return None
    return current


class BaseFileSerializer(ResourceSerializer):
    def __init__(self, is_dir=False):
        self.is_dir = is_dir

    @staticmethod
    def output_path(path: str, id: Optional[str]) -> str:
        """`path` of a file output; for a folder (ending with a slash) the file in it named as the last part of `id`"""
        if path.endswith('/') or path.endswith('\\'):
            path += id.replace('\\', '/').rsplit('/', 1)[-1]
        return path

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        os.makedirs(path if self.is_dir else os.path.dirname(path), exist_ok=True)
        return []


class PlainBinarySerializer(BaseFileSerializer):
    ui = UiSerialization('binary', suffix='.bin', reversible=True)

    def __init__(self):
        super().__init__(is_dir=False)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        path = self.output_path(path, id)
        super().serialize(data, path)
        output_path = f'{path}.bin'
        with open(output_path, 'wb') as file:
            file.write(data)
        return [output_path]

    def deserialize(self, file_paths: List[str], id=None, block=None, **kwargs):
        if len(file_paths) != 1:
            raise Exception('Import one file')
        with open(file_paths[0], 'rb') as file:
            return file.read()


def write_skipped(path: str, skipped: List[Tuple[str, str]]) -> List[str]:
    """`skipped.txt` in the folder `path`, a line "<name>\t\t<error>" per resource not exported (nothing without one)"""
    if not skipped:
        return []
    file_path = path_join(path, 'skipped.txt')
    with open(file_path, 'w') as f:
        for item in skipped:
            f.write('%s\t\t%s\n' % item)
    return [file_path]


def export_child(output: list, skipped: list, block, data, path: str, name: str, id: str, **kwargs) -> bool:
    """Exports an archive item (`data` of `block`, resource `id`) to `path` with its serializer, its files added to
    `output`; a failure goes to `skipped` as (`name`, error). True when exported"""
    from serializers import get_serializer

    try:
        output.extend(get_serializer(block, data).serialize(data, path, block=block, id=id, **kwargs))
        return True
    except Exception as ex:
        traceback.print_exc()
        skipped.append((name, format_exception(ex)))
        return False


def unique_name(name: str, taken: set, ignore_case: bool = False) -> str:
    """`name`, with 0, 1... appended while it is in `taken` (which holds lower case names with `ignore_case`)"""
    result, n = name, 0
    while (result.lower() if ignore_case else result) in taken:
        result = f'{name}{n}'
        n += 1
    return result
