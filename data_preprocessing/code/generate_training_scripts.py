import argparse
import os
import pandas as pd

from itertools import permutations


def get_assembly_list(input_dir: str, input_prefix: str):
    return set(
        x.split(input_prefix)[1].split(".")[1]
        for x in list(
            filter(
                lambda x: x.startswith(input_prefix),
                os.listdir(f"{input_dir}/{input_prefix}"),
            )
        )
    )


def generate_training_scripts(
    dir_input: str,
    dir_models: str,
    model_params: str,
    dir_output: str,
):
    for root_entry in sorted(os.scandir(dir_input), key=lambda x: x.name):
        input_prefix = root_entry.name

        print(f"Generating run scripts for {input_prefix}")

        out_script_name = f"{dir_output}/{input_prefix}/train.run"
        if os.path.exists(out_script_name):
            os.remove(out_script_name)

        assembly_list = get_assembly_list(dir_input, input_prefix)

        model_params_df = pd.read_csv(model_params).set_index("model")
        for it in ["bottleneck-dim", "iters-per-epoch", "pretrain-epochs"]:
            model_params_df[it] = model_params_df[it].astype(pd.Int64Dtype())

        with open(out_script_name, "a") as f_out:
            for model in model_params_df.index:
                for source_genome, target_genome in permutations(assembly_list, 2):
                    src_data_prefix = f"{input_prefix}.{source_genome}"
                    tgt_data_prefix = f"{input_prefix}.{target_genome}"

                    cmd_run = (
                        f"python3 {dir_models}/{model}.py "
                        f"-d {input_prefix}.{source_genome}.{target_genome} "
                        f"-c datasets "
                        f"--source-positive {src_data_prefix}.fa "
                        f"--source-negative {src_data_prefix}.random.fa "
                        f"--target-train {tgt_data_prefix}.random_2x.fa "
                        f"--target-positive {tgt_data_prefix}.fa "
                        f"--target-negative {tgt_data_prefix}.random.fa "
                        f"-a hybrid "
                        f"--scratch "
                        f"--seed {model_params_df.loc[model,'seed']} "
                        f"--epochs {model_params_df.loc[model,'epochs']} "
                        f"--log {model if model != 'erm' else 'src_only'}-{input_prefix}.{source_genome}.{target_genome}-seed-{model_params_df.loc[model,'seed']} "
                    )

                    for param in [
                        "bottleneck-dim",
                        "trade-off-norm",
                        "trade-off",
                        "iters-per-epoch",
                        "pretrain-epochs",
                    ]:
                        param_value = model_params_df.loc[model, param]
                        if not pd.isna(param_value):
                            cmd_run += f" --{param} {param_value}"

                    f_out.write(" ".join(cmd_run.split()) + "\n")


def main(args: argparse.Namespace):
    generate_training_scripts(
        args.input_dir,
        args.models_dir,
        args.model_params,
        args.output_dir,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a script to run every model of Domain Adaptation."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=str,
        required=True,
        metavar="PATH",
        help="Input directory with all necessary fasta files.",
    )
    parser.add_argument(
        "-m",
        "--models-dir",
        type=str,
        required=True,
        metavar="PATH",
        help="Input directory with model script.",
    )
    parser.add_argument(
        "-p",
        "--model-params",
        type=str,
        required=True,
        metavar="PATH",
        help="Path to a .csv table with model parameters.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        metavar="PATH",
        help="Output directory for a script.",
    )

    args = parser.parse_args()
    main(args)
