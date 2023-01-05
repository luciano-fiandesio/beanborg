# -*- coding: utf-8 -*-
import re
class StringUtils:

    def strip_digits(str):
        #return ''.join([c for c in str if not c.isdigit()])
        return re.sub("[^A-Z ]", "", str)
