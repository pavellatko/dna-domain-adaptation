import os
import argparse
import pandas as pd

from utils.cmdrun import cmdrun


def check_lengths(path: str):
    return (
        pd.read_table(path, header=None)
        .assign(length=lambda x: x[2] - x[1])["length"]
        .nunique()
    )


def test_preprocessed_files(original: str, randomized: str):
    if not os.path.exists(f"{original}"):
        print(f"No data for: {original}")
        return

    same_length_original = check_lengths(f"{original}")
    assert same_length_original == 1, "Original file contains different region lengths!"

    same_length_randomized = check_lengths(f"{randomized}")
    assert (
        same_length_randomized == 1
    ), "Randomized file contains different region lengths!"

    sp = cmdrun(
        f"bedtools intersect -a {original} -b {randomized} -u | wc -l", shell=True
    )
    intersection_size = int(sp.stdout.decode("UTF-8"))
    assert intersection_size == 0, "Original file overlaps the randomized!"


def main(args):
    test_preprocessed_files(
        original=args.original_file, randomized=args.randomized_file
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test preprocessing stage..")

    parser.add_argument(
        "-a",
        "--original-file",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to an original file.",
    )
    parser.add_argument(
        "-b",
        "--randomized-file",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to a randomized file.",
    )

    args = parser.parse_args()
    main(args)
