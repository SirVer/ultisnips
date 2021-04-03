import unittest
from UltiSnips.text import *

class TestUltiSnipsText(unittest.TestCase):

    def test_unescape(self):
        self.assertEqual(unescape('A\\ Vim\\ Command'), 'A\\ Vim\\ Command')

    def test_fill_in_whitespace(self):
        self.assertEqual(fill_in_whitespace(r'\t  words\t'), '\t words\t')
        self.assertEqual(
                fill_in_whitespace(r'\n\a  \t More\b\aWhitespace\n'), 
                '\n\a  \t More\b\aWhitespace\n')

    def test_head_tail(self):
        self.assertEqual(head_tail('SomeText'), ('SomeText', ''))
        self.assertEqual(head_tail('Some Text'), ('Some', 'Text'))
        self.assertEqual(head_tail('\t\tif var is None:'), ('if', 'var is None:'))
        self.assertEqual(head_tail('\n\t  AFuncMethod():\n'), ('AFuncMethod()', ''))


if __name__ == "__main__": 
    unittest.main()
