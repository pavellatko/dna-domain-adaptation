import argparse
import logging
import math
import os
import pandas as pd
import tempfile

from utils.cmdrun import cmdrun

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_fasta_from_bed(
    bedtools_bin: str, bed_input: str, dir_genome: str, assembly: str
):
    fasta_output = bed_input.replace(".bed", ".fa")
    with open(fasta_output, "w") as f_out:
        cmdrun(
            f"{bedtools_bin} getfasta -fi {dir_genome}/{assembly}.fa -bed {bed_input}",
            stdout=f_out,
        )


def make_uniform_lengths(s: pd.Series, length: int):
    difference = (s[2] - s[1] - length) / 2
    if difference > 0:
        return pd.Series(
            [s[0], s[1] + math.floor(difference), s[2] - math.ceil(difference)],
            index=s.index,
            name=s.name,
        )
    return pd.Series(pd.NA, index=s.index, name=s.name)


def preprocess_bed(
    dir_input: str,
    dir_output: str,
    dir_genome: str,
    length: int,
    get_fasta: bool,
    bedtools_bin: str,
):
    for root_entry in sorted(os.scandir(dir_input), key=lambda x: x.name):
        preprocessed_dir = f"{dir_output}/{root_entry.name.rsplit('.', maxsplit=1)[0]}"
        os.makedirs(preprocessed_dir, exist_ok=True)

        bed_output = f"{preprocessed_dir}/{root_entry.name}.bed"
        if os.path.exists(bed_output):
            logger.warning(
                f"Already exists, so skipping: {os.path.basename(bed_output)}"
            )
            continue

        print(f"Preprocessing {root_entry.name:36}", end="\t")

        experiment_list = [
            f"{root_entry.path}/{x}" for x in os.listdir(root_entry.path)
        ]
        sp1 = cmdrun(f"cat {' '.join(experiment_list)}")
        sp2 = cmdrun(f"cut -f1,2,3", input=sp1.stdout)
        sp3 = cmdrun(f"sort -k1,1 -k2,2n", input=sp2.stdout)
        sp4 = cmdrun(f"{bedtools_bin} merge -i stdin", input=sp3.stdout)

        assembly = root_entry.name.rsplit(".", maxsplit=1)[1]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_bed_input = f"{tmpdir}/tmp.bed"
            with open(tmp_bed_input, "w") as f_out:
                cmd = f"{bedtools_bin} slop -i stdin -g {dir_genome}/{assembly}.chrom.sizes -b {str(length // 2)}"
                cmdrun(cmd, input=sp4.stdout, stdout=f_out)

            output_df = (
                pd.read_table(tmp_bed_input, header=None)
                .apply(lambda x: make_uniform_lengths(x, length), axis=1)
                .dropna()
            )
            output_df.to_csv(bed_output, sep="\t", header=False, index=False)

            size_input = int(
                cmdrun(f"wc -l {tmp_bed_input}", shell=True)
                .stdout.decode("utf-8")
                .split()[0]
            )
            size_output = int(
                cmdrun(f"wc -l {bed_output}", shell=True)
                .stdout.decode("utf-8")
                .split()[0]
            )
            print(
                f"#{size_input:>7,d} -> #{size_output:>7,d} (-{(size_input-size_output)/size_input:>4.2%})."
            )

            if get_fasta:
                get_fasta_from_bed(bedtools_bin, bed_output, dir_genome, assembly)


def main(args):
    preprocess_bed(
        dir_input=args.dir_input,
        dir_output=args.dir_output,
        dir_genome=args.dir_genome,
        length=args.length,
        get_fasta=args.get_fasta,
        bedtools_bin=args.bedtools_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate DNA datasets for Domain Adaptation."
    )

    parser.add_argument(
        "-i",
        "--dir-input",
        type=str,
        required=True,
        metavar="PATH",
        help="Input directory path with raw data.",
    )
    parser.add_argument(
        "-o",
        "--dir-output",
        type=str,
        required=True,
        metavar="PATH",
        help="Output directory path for preprocessed data..",
    )
    parser.add_argument(
        "-g",
        "--dir-genome",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to directory with genome files.",
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=1_000,
        help="Uniform window length (default 1000).",
    )
    parser.add_argument(
        "-f", "--get-fasta", action="store_true", help="Generate output .fasta file."
    )
    parser.add_argument(
        "-p",
        "--bedtools-path",
        type=str,
        default="bedtools",
        help="Path to bedtools binary.",
    )

    args = parser.parse_args()
    main(args)
