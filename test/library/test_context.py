import unittest

from library.context import DocumentationContext


class TestDocumentationCtxData(unittest.TestCase):
    def test_expressions(self):
        ctx = DocumentationContext()
        width, height = ctx.data('width'), ctx.data('height')
        self.assertEqual(str(width * height), 'width*height')
        self.assertEqual(str((width + 1) * height), '(width+1)*height')
        self.assertEqual(str(2 * (width - 1)), '2*(width-1)')
        self.assertEqual(str((width - 1) // (height * 2)), '(width-1)/(height*2)')
        self.assertEqual(str(4 + ctx.data('../count')), '4+^count')
        self.assertEqual(str(width & 0xF), 'width & 15')

    def test_shift_brackets(self):
        # each operand is put in brackets by its own operators
        ctx = DocumentationContext()
        self.assertEqual(str((ctx.data('a') - 1) << ctx.data('b')), '(a-1) << b')
        self.assertEqual(str(ctx.data('a') >> (ctx.data('b') + 1)), 'a >> (b+1)')
        self.assertEqual(str(1 << (ctx.data('b') * 2)), '1 << (b*2)')

    def test_comparisons(self):
        ctx = DocumentationContext()
        self.assertEqual(str(ctx.data('version') >= 3), 'version >= 3')
        self.assertEqual(str(3 < ctx.data('version')), 'version > 3')
        self.assertEqual(str(ctx.data('tag') != 'end'), 'tag != end')
