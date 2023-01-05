# -*- coding: utf-8 -*-

import hashlib

def hash(csv_row):

    return hashlib.md5(",".join(csv_row).encode("utf-8")).hexdigest()
