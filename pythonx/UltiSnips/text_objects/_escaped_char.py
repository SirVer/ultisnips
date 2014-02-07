#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.text_objects._base import NoneditableTextObject

class EscapedChar(NoneditableTextObject):
    """
    This class is a escape char like \$. It is handled in a text object to make
    sure that siblings are correctly moved after replacing the text.

    This is a base class without functionality just to mark it in the code.
    """
    pass

