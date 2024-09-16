import argparse


def eval_args(help_message):

    parser = argparse.ArgumentParser(description=help_message)

    parser.add_argument(
        "-f",
        "--file",
        help="Configuration file to load",
        required=True,
    )

    parser.add_argument(
        "-v", "--debug", required=False, default=False, action="store_true"
    )

    args = parser.parse_args()
    return args
