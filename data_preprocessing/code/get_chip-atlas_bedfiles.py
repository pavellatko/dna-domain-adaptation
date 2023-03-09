import argparse
import logging
import tempfile
import pandas as pd

from utils.cmdrun import cmdrun

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_experimental_filtered_data(
    experimentlist_path: str,
    antigen_class: str,
    genome_assemblies: list,
):
    no_peaks_thr = 50_000
    return (
        pd.read_table(
            experimentlist_path,
            header=None,
            usecols=range(8),
            names=[
                "experimental_id",
                "genome_assembly",
                "antigen_class",
                "antigen",
                "cell_type_class",
                "cell_type",
                "cell_type_description",
                "processing_logs",
            ],
        )
        .assign(
            no_peaks=lambda x: x["processing_logs"]
            .str.split(",", expand=True)[3]
            .astype(int)
        )
        .drop(columns=["cell_type_description", "processing_logs"])
        .query(
            " and ".join(
                [
                    f"genome_assembly in {genome_assemblies}",
                    f'antigen_class.str.contains("{antigen_class}")',
                    f"{no_peaks_thr*1.25} >= no_peaks >= {no_peaks_thr*.5}",
                    f"cell_type_class not in  ['Others', 'Unclassified']",
                ]
            ),
            engine="python",
        )
        .assign(
            antigen=lambda x: x.antigen.str.upper(),
            no_assemblies_by_cell_type=lambda x: x.groupby(
                ["antigen_class", "antigen", "cell_type_class", "cell_type"]
            )["genome_assembly"].transform("nunique"),
        )
        .query("no_assemblies_by_cell_type > 1")
        .sort_values("no_peaks", ascending=False)
        .groupby(["cell_type_class", "cell_type", "antigen", "genome_assembly"])
        .head(1)
        .sort_values(
            ["antigen", "cell_type_class", "cell_type", "genome_assembly", "no_peaks"]
        )
        .reset_index(drop=True)
    )


def get_chipatlas_bedfiles(
    antigen_class: str,
    genome_assemblies: list,
    experimentlist_path: str,
    output_dir: str,
    threshold: str,
):
    experimentlist_df = get_experimental_filtered_data(
        experimentlist_path,
        antigen_class,
        genome_assemblies,
    )
    experimentlist_df.to_csv(
        f"experiment_data.{antigen_class}.{experimentlist_df.shape[0]}_experiments.csv",
        index=False,
    )

    with pd.option_context("display.max_rows", None):
        print(
            experimentlist_df.drop(
                columns=["antigen_class", "no_assemblies_by_cell_type"]
            )
        )

    print("Downloading experiment files from ChIP-atlas")

    cmd_list = ""
    for _, row in experimentlist_df.iterrows():
        cmd = f"-P {output_dir}/{row.antigen_class[:3]}.{row.antigen}.{row.cell_type_class.replace(' ', '_')}.{row.cell_type.replace(' ', '_')}.{row.genome_assembly} http://dbarchive.biosciencedbc.jp/kyushu-u/{row.genome_assembly}/eachData/bed{threshold}/{row.experimental_id}.{threshold}.bed"
        cmd_list += cmd + "\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd_list_tmpfile = f"{tmpdir}/cmd_list.tmp"
        with open(cmd_list_tmpfile, "w") as f_out:
            f_out.write(cmd_list)
        cmdrun(
            f"cat {cmd_list_tmpfile} | xargs -n 3 -P 8 wget -c -q",
            shell=True,
            capture_output=False,
        )


def main(args: argparse.Namespace):
    get_chipatlas_bedfiles(
        args.antigen_class,
        args.genome_assembly,
        args.experimentlist,
        args.output_dir,
        args.threshold,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract ChIP-Atlas data.")

    parser.add_argument(
        "--antigen-class",
        type=str,
        required=True,
        choices=["Histone", "TFs"],
        help="Input antigen class",
    )
    parser.add_argument(
        "--genome-assembly",
        type=str,
        nargs="+",
        default=["ce11", "dm6", "hg38", "mm10", "sacCer3"],
        help='Genome assemblies (default ["ce11", "dm6", "hg38", "mm10", "sacCer3"]).',
    )
    parser.add_argument(
        "--threshold",
        type=str,
        default="05",
        choices=["05", "10", "20"],
        help='ChIP-Atlas Q-value threshold (default "05").',
    )
    parser.add_argument(
        "--experimentlist",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to experimentList.tab",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to the output directory.",
    )

    args = parser.parse_args()
    main(args)
