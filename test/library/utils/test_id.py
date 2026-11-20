import os
import shutil
import tempfile
import unittest

from library import require_resource
from library.loader import clear_file_cache
from library.utils.id import id_to_path, is_file_id, join_id, path_to_name, split_id, split_last_id_part

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')


class TestIds(unittest.TestCase):
    def test_file_path_escaped(self):
        file_id = path_to_name('C:\\games\\my__mods\\TR1.FSH')
        self.assertEqual(file_id, 'C---DRIVE/games/my_%5Fmods/TR1.FSH')
        self.assertTrue(is_file_id(file_id))
        self.assertEqual(id_to_path(file_id), 'C:/games/my__mods/TR1.FSH')
        self.assertEqual(id_to_path(join_id(file_id, 'children', '3', 'item', 'data')), 'C:/games/my__mods/TR1.FSH')

    def test_split(self):
        self.assertEqual(split_id('/g/TR1.FSH'), ('/g/TR1.FSH', ''))
        self.assertEqual(split_id('/g/TR1.FSH__children/3/item/data'), ('/g/TR1.FSH', 'children/3/item/data'))
        self.assertEqual(split_id('/g/TR1.FSH__uncompressed'), ('/g/TR1.FSH', 'uncompressed'))
        self.assertFalse(is_file_id('/g/TR1.FSH__children'))

    def test_file_name_ending_in_underscore(self):
        file_id = path_to_name('/g/TRACK_')
        item_id = join_id(file_id, 'children', '0')
        self.assertEqual(item_id, '/g/TRACK___children/0')
        self.assertEqual(split_id(item_id), ('/g/TRACK_', 'children/0'))
        self.assertEqual(id_to_path(item_id), '/g/TRACK_')
        self.assertEqual(split_last_id_part(join_id(file_id, 'children')), ('/g/TRACK_', 'children'))

    def test_join(self):
        self.assertEqual(join_id('/g/F', 'children', '3'), '/g/F__children/3')
        self.assertEqual(join_id('/g/F__children/3', 'item', 'data'), '/g/F__children/3/item/data')

    def test_split_last_part(self):
        self.assertEqual(split_last_id_part('/g/F__children/3/item'), ('/g/F__children/3', 'item'))
        self.assertEqual(split_last_id_part('/g/F__children'), ('/g/F', 'children'))
        self.assertEqual(split_last_id_part('/g/F'), ('/g', 'F'))


class TestRequireResource(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.original = os.path.join(SAMPLES, 'ZAL1_POR.FAM').replace('\\', '/')
        # a folder with `__` and a file name ending in `_`
        folder = os.path.join(self.tmp, 'my__mods')
        os.makedirs(folder)
        self.copy = os.path.join(folder, 'ZAL1_POR_').replace('\\', '/')
        shutil.copy(self.original, self.copy)

    def tearDown(self):
        clear_file_cache(self.copy)
        clear_file_cache(self.original)
        shutil.rmtree(self.tmp)

    def test_item_of_a_file_with_underscores(self):
        (_, block, data), (file_id, _, _) = require_resource(join_id(path_to_name(self.copy), 'children', '0'))
        (_, original_block, original_data), _ = require_resource(join_id(path_to_name(self.original), 'children', '0'))
        self.assertEqual(file_id, path_to_name(self.copy))
        self.assertIs(type(block), type(original_block))
        self.assertEqual(data, original_data)


if __name__ == '__main__':
    unittest.main()
