import os
import shutil
import tempfile
import unittest

from api.endpoints.file_api import FileAPI
from library import require_file
from library.loader import clear_file_cache
from library.new_files import NEW_FILE_FORMATS, NEW_FILE_GAMES, NEW_FILE_KINDS, data_class_name, new_file_formats
from serializers.misc.json_utils import convert_bytes, serialize_exceptions


class TestNewFiles(unittest.TestCase):
    """Every format of the New file dialog: a new file under its default name (in its folder) opens as the same block
    and writes back to the same bytes"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.file_api = FileAPI(api=None)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _path(self, fmt, folder=True) -> str:
        directory = os.path.join(self.tmp_dir, fmt.id, *(fmt.folder.split('/') if folder and fmt.folder else []))
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, fmt.file_name)

    def test_new_files_read_back(self):
        for fmt in NEW_FILE_FORMATS:
            with self.subTest(fmt.id):
                path = self._path(fmt)
                self.file_api.create_new_file(path, fmt.id)
                with open(path, 'rb') as f:
                    written = f.read()
                try:
                    _, block, data = require_file(path, lazy=False)
                    self.assertEqual(data_class_name(block, data), fmt.data_class_name)
                    self.assertEqual(block.pack(data), written)
                    # what open_file sends to the GUI
                    convert_bytes(block.schema)
                    convert_bytes(serialize_exceptions(data))
                finally:
                    clear_file_cache(path)

    def test_templates(self):
        from resources.eac.archives import WwwwBlock

        def items(data):
            block = WwwwBlock()
            return [
                (type(block.item_block.possible_blocks[c['item']['choice_index']]).__name__, c['item']['data'])
                for c in data['children']
            ]

        for fmt_id, expected in [
            ('cfm', ['OripGeometry', 'ShpiBlock', 'OripGeometry', 'ShpiBlock']),
            ('fam', ['WwwwBlock', 'WwwwBlock', 'ShpiBlock', 'WwwwBlock']),
        ]:
            with self.subTest(fmt_id):
                fmt = next(f for f in NEW_FILE_FORMATS if f.id == fmt_id)
                path = self._path(fmt)
                self.file_api.create_new_file(path, fmt.id)
                try:
                    _, _, data = require_file(path, lazy=False)
                    read = items(data)
                    self.assertEqual([name for name, _ in read], expected)
                    if fmt_id == 'cfm':
                        self.assertEqual([d['shpi_dir'] for name, d in read if name == 'ShpiBlock'], ['WRAP', 'WRAP'])
                    else:
                        self.assertEqual(
                            [[n for n, _ in items(d)] for n, d in read if n == 'WwwwBlock'],
                            [['ShpiBlock'], ['ShpiBlock'], []],
                        )
                finally:
                    clear_file_cache(path)

    def test_refuses_path_not_recognised(self):
        fmt = next(f for f in NEW_FILE_FORMATS if f.id == 'nfs6_car_ini')
        path = self._path(fmt, folder=False)
        with open(path, 'w') as f:
            f.write('kept')
        with self.assertRaisesRegex(ValueError, 'Cars/<car>'):
            self.file_api.create_new_file(path, fmt.id)
        with open(path) as f:
            self.assertEqual(f.read(), 'kept')

    def test_formats_for_gui(self):
        res = new_file_formats()
        formats = res['formats']
        self.assertEqual(len({f['id'] for f in formats}), len(NEW_FILE_FORMATS))
        game_ids = [g['id'] for g in res['games']]
        self.assertEqual(game_ids, [id for id, _ in NEW_FILE_GAMES])
        self.assertEqual(res['kinds'], NEW_FILE_KINDS)
        for f in formats:
            self.assertTrue(f['games'] and set(f['games']) <= set(game_ids), f['id'])
            self.assertIn(f['kind'], NEW_FILE_KINDS)
        # every game offers something
        self.assertEqual({g for f in formats for g in f['games']}, set(game_ids))
        qfs = next(f for f in formats if f['id'] == 'qfs')
        self.assertTrue(qfs['block_class_mro'].startswith('ShpiBlock__'))
