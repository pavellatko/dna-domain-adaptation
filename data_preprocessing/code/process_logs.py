import argparse
import itertools
import functools
import json

import numpy as np
import plotly.express as px
import pandas as pd


def add_metric_val(metrics: dict, dataset: str, method: str, metric_name: str, metric_val: float) -> None:
    method = method.split('-')[0]
    if dataset not in metrics:
        metrics[dataset] = {}
    if method not in metrics[dataset]:
        metrics[dataset][method] = {}
    if metric_name not in metrics[dataset][method]:
        metrics[dataset][method][metric_name] = []
    metrics[dataset][method][metric_name].append(metric_val)


def main(args: argparse.Namespace):
    train_params = None
    metrics = {}
    for line in itertools.chain.from_iterable(map(open, args.logs)):
        if line.startswith('Namespace('):
            line = line.replace('Namespace', 'dict')
            train_params = eval(line)
        else:
            if line.startswith(' * Acc@1'):
                acc = float(line.split()[-1])
                add_metric_val(metrics, train_params['data_name'], train_params['log'], 'accuracy', acc)
            elif line.startswith(' * Acc1'):
                acc = float(line.split()[2])
                add_metric_val(metrics, train_params['data_name'], train_params['log'], 'accuracy', acc)
            elif line.startswith('PR AUC') or line.startswith('F1 PR AUC'):
                pr_auc = float(line.split()[-1])
                add_metric_val(metrics, train_params['data_name'], train_params['log'], 'pr_auc', pr_auc)
            elif line.startswith('ROC AUC') or line.startswith('F1 ROC AUC'):
                roc_auc = float(line.split()[-1])
                add_metric_val(metrics, train_params['data_name'], train_params['log'], 'roc_auc', roc_auc)
    if args.metrics:
        print('Metrics')
        print(json.dumps(metrics, indent=4))
    if args.csv:
        total_dfs = dict()
        for ds_name, ds in metrics.items():
            print('Dataset', ds_name)
            cur_metrics = None

            result = []

            for method_name, method_data in ds.items():
                if cur_metrics is None:
                    cur_metrics = list(method_data.keys())
                row = dict(zip(['method', *cur_metrics],
                               [method_name] +
                               [f'{np.mean(method_data[metric]):.3f}' for metric in cur_metrics]))
                if method_name == 'src_only':
                    result.insert(0, row)
                else:
                    result.append(row)
            df = pd.DataFrame(result).set_index('method').astype(float)

            if ds_name not in total_dfs.keys():
                total_dfs[ds_name] = df.sort_index()
            else:
                total_dfs[ds_name] = pd.concat([total_dfs[ds_name], df]).sort_index()
        
        path_output = list(total_dfs.keys())[0].rsplit(".", maxsplit=2)[0]

        resulting_df = functools.reduce(lambda x, y: pd.concat([x, y], axis=1), total_dfs.values())
        resulting_df.columns = pd.MultiIndex.from_product([[k for k in total_dfs.keys()], list(total_dfs.values())[0].columns], names=['data', 'metric_type'])
        resulting_df.to_csv(f"{path_output}.tsv", sep='\t')

        plotly_df = pd.DataFrame()
        for data_name, data_df in total_dfs.items():
            reference = data_df.loc["src_only", :].to_frame().T
            reference.index.name = "method"

            diff_df = (
                pd.DataFrame(
                    np.subtract(data_df.values, reference.values),
                    index=data_df.index,
                    columns=data_df.columns,
                ).iloc[:-1,:]
                .reset_index()
                .assign(data_name="->".join(data_name.rsplit(".", maxsplit=2)[-2:]))
                .melt(
                    id_vars=["data_name", "method"],
                    value_vars=["accuracy", "pr_auc", "roc_auc"],
                    var_name='metric',
                    value_name='diff'
                )
            )

            plotly_df = pd.concat([plotly_df, diff_df])

        plotly_df = plotly_df.sort_values(['data_name', 'method','metric'], ascending=[False, True, True])

        fig = px.bar(
            plotly_df,
            facet_col="data_name",
            x="metric",
            y="diff",
            color="method",
            barmode="group",
        )
        fig.update_layout(
            title=f'{path_output}',
            height=400,
            width=1800,
            margin=dict(l=10, r=10, t=50, b=10),
        )

        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.for_each_xaxis(lambda y: y.update(title=""))
        fig.add_annotation(
            y=-0.25,
            x=0.5,
            text="metric",
            xref="paper",
            yref="paper",
            showarrow=False,
        )

        fig.write_html(f"{path_output}.html")
        fig.write_image(f"{path_output}.png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv', action='store_true', help='print csv with mean metrics')
    parser.add_argument('-m', '--metrics', action='store_true', help='print all metrics in json format')
    parser.add_argument('logs', metavar='LOGS', type=str, nargs='+',
                        help='test logs')
    main(parser.parse_args())