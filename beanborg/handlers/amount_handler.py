__copyright__ = "Copyright (C) 2022  Luciano Fiandesio"
__license__ = "GNU GPLv2"

from beancount.core.number import D


class AmountHandler:

    # create mapping tables for currency conversion
    sign_trans = str.maketrans({'$': '', ' ': ''})  # remove $ and space
    dot_trans = str.maketrans({'.': '', ',': ''})  # remove . and ,

    def handle(self, val, args):

        if args.indexes.amount_in:
            return self.__convert(
                val[args.indexes.amount_in].strip()) - self.__convert(val)

        if args.rules.invert_negative and val[0] == "-":
            val = val.replace("-", "+")

        if args.rules.force_negative == 1 and val[0].isdigit():
            val = "-" + val

        return self.__convert(val)

    def __convert(self, num, sign_trans=sign_trans, dot_trans=dot_trans):
        """
        Converts the given string into a decimal, where the last
        two digits are always assumed to be the decimals:

        "22 000,76"      -> 22000.76
        "22.000,76"      -> 22000.76
        "22,000.76"      -> 22000.76
        "1022000,76"     -> 1022000.76
        "-1,022,000.76", -> -1022000.76
        "1022000",       -> 1022000.0
        "22 000,76$",    -> 22000.76
        "$22 000,76"     -> 22000.76

        """

        num = num.translate(sign_trans)
        num = num[:-3].translate(dot_trans) + num[-3:]
        return D(num.replace(',', '.'))
