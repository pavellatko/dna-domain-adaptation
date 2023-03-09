import argparse
import os
import tempfile
import logging

from utils.cmdrun import cmdrun
from preprocess_bed import get_fasta_from_bed
from test_preprocessed_files import test_preprocessed_files

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_bedtools_shuffle(
    bedtools_bin: str, bed_input: str, exclude: str, chrom_sizes: str, f_out
):
    return cmdrun(
        cmd=(
            f"{bedtools_bin} shuffle "
            f"-i {bed_input} -excl {exclude} -g {chrom_sizes} "
            f"-seed 42 -maxTries 1000000 -noOverlapping"
        ),
        stdout=f_out,
    )


def generate_random_samples(
    dir_input: str,
    dir_genome: str,
    dir_gap: str,
    get_fasta: bool,
    bedtools_bin: str,
):
    for root_entry in sorted(os.scandir(dir_input), key=lambda x: x.name):
        for bed_input in sorted(os.listdir(root_entry.path)):
            if ".fa" in bed_input or "random" in bed_input:
                continue

            bed_input_path = f"{root_entry.path}/{bed_input}"
            bed_output_path = bed_input_path.replace(".bed", ".random.bed")
            if os.path.exists(bed_output_path):
                logger.warning(f"Already exists, so skipping: {bed_input}")
                continue

            print(f"Generating random samples for {bed_input}")

            assembly = bed_input.rsplit(".", maxsplit=2)[-2]
            bed_output_2x_path = (
                f"{root_entry.path}/{bed_input.replace('.bed', '.random_2x.bed')}"
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                bed_exclude_path = f"{tmpdir}/excl.bed"
                bed_input_2x_path = f"{tmpdir}/input2x.bed"

                with open(bed_exclude_path, "w") as f_out:
                    cmdrun(
                        f"cat {bed_input_path} {dir_gap}/{assembly}.gap.txt",
                        stdout=f_out,
                    )
                with open(bed_input_2x_path, "w") as f_out:
                    cmdrun(f"cat {bed_input_path} {bed_input_path}", stdout=f_out)

                with open(bed_output_path, "w") as f_out:
                    run_bedtools_shuffle(
                        bedtools_bin,
                        bed_input_path,
                        bed_exclude_path,
                        f"{dir_genome}/{assembly}.chrom.sizes",
                        f_out,
                    )
                with open(bed_output_2x_path, "w") as f_out:
                    run_bedtools_shuffle(
                        bedtools_bin,
                        bed_input_2x_path,
                        bed_exclude_path,
                        f"{dir_genome}/{assembly}.chrom.sizes",
                        f_out,
                    )

                test_preprocessed_files(bed_input_path, bed_output_path)
                test_preprocessed_files(bed_input_path, bed_output_2x_path)

                if get_fasta:
                    get_fasta_from_bed(
                        bedtools_bin, bed_output_path, dir_genome, assembly
                    )
                    get_fasta_from_bed(
                        bedtools_bin, bed_output_2x_path, dir_genome, assembly
                    )


def main(args: argparse.Namespace):
    generate_random_samples(
        dir_input=args.dir_input,
        dir_gap=args.dir_gap,
        dir_genome=args.dir_genome,
        get_fasta=args.get_fasta,
        bedtools_bin=args.bedtools_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate DNA datasets for Domain Adaptation"
    )
    parser.add_argument(
        "-i",
        "--dir-input",
        type=str,
        required=True,
        help="Input directory path with preprocessed data.",
    )
    parser.add_argument(
        "-g",
        "--dir-genome",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to a directory with genome files.",
    )
    parser.add_argument(
        "--dir-gap",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to a directory with gap files.",
    )
    parser.add_argument(
        "-f",
        "--get-fasta",
        action="store_true",
        help="Convert the resulting .bed file to .fasta.",
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
