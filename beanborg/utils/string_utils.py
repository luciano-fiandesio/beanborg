# -*- coding: utf-8 -*-
import re


class StringUtils:
    """Utility functions for strings."""
    @staticmethod
    def strip_digits(str):
        """Strip digits from a string."""
        return re.sub("[^A-Z ]", "", str)
