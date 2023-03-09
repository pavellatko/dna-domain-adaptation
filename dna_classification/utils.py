"""
@author: Junguang Jiang, Baixu Chen
@contact: JiangJunguang1123@outlook.com, cbx_99_hasta@outlook.com
"""
import os
import sys
import time

import numpy as np
import timm
import torch
import torch.nn as nn
import torch.nn.functional as F
from Bio import SeqIO
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve, roc_curve, auc
from torch.utils.data.dataset import Dataset

sys.path.append('../../..')
import models
from tllib.utils.metric import accuracy, ConfusionMatrix
from tllib.utils.meter import AverageMeter, ProgressMeter

from tqdm.auto import tqdm


def get_model_names():
    return sorted(
        name for name in models.__dict__
        if name.islower() and not name.startswith("__")
        and callable(models.__dict__[name])
    ) + timm.list_models()


def get_model(model_name):
    if model_name in models.__dict__:
        # load models from tllib.vision.models
        backbone = models.__dict__[model_name]()
    else:
        raise ValueError(f"unknown model {model_name}")
    return backbone


def onehot_seq(seq, data, ind):
    NUCS = "atgc"

    seq = np.array(list(seq))
    for i, nuc in enumerate(NUCS):
        data[ind, seq == nuc, i] = 1


def read_fasta(path: str):
    with open(path) as f:
        num_lines = sum(1 for line in f)

    data = None
    cur_ind = 0
    for ind, record in tqdm(enumerate(SeqIO.parse(path, "fasta"))):
        if data is None:
            data = np.zeros((num_lines, len(record), 4), dtype=np.int8)
        seq = record.seq.lower()
        if len(seq) != data.shape[1]:
            continue
        if "n" in seq:
            continue
        onehot_seq(seq, data, cur_ind)
        cur_ind += 1
    data = data[:cur_ind]
    return data


class SeqDataset(Dataset):
    def __init__(self, data, labels=None):
        self.data = torch.tensor(data, dtype=torch.int8)
        self.labels = None
        if labels is not None:
            self.labels = torch.tensor(labels, dtype=torch.int8)

    def __getitem__(self, index):
        if self.labels is not None:
            return self.data[index].float(), self.labels[index].long()
        else:
            return self.data[index].float(), np.nan

    def __len__(self):
        return self.data.shape[0]


def get_train_datasets(source_positive: str, source_random: str, target_train_random: str,
                       dataset_name=None, cache_dir=None, trim_random=True, train_size=0.8, random_state=42):
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    if dataset_name:
        if dataset_name in os.listdir(cache_dir):
            path = os.path.join(cache_dir, dataset_name)
            src_train_dataset = torch.load(os.path.join(path, 'src_train_dataset'))
            tgt_train_dataset = torch.load(os.path.join(path, 'tgt_train_dataset'))
            src_test_dataset = torch.load(os.path.join(path, 'src_test_dataset'))
            return src_train_dataset, tgt_train_dataset, src_test_dataset

    src_pos = read_fasta(source_positive)
    src_random = read_fasta(source_random)
    if trim_random:
        src_random = src_random[:src_pos.shape[0]]
    src_data = np.concatenate([src_pos, src_random], axis=0)
    src_labels = np.concatenate([
        np.ones(src_pos.shape[0]),
        np.zeros(src_random.shape[0])
    ], axis=0)
    src_data_train, src_data_test, src_lbl_train, src_lbl_test = train_test_split(src_data, src_labels,
                                                                                  train_size=train_size, shuffle=True,
                                                                                  random_state=random_state)
    src_train_dataset = SeqDataset(src_data_train, src_lbl_train)
    src_test_dataset = SeqDataset(src_data_test, src_lbl_test)

    tgt_train_rnd = read_fasta(target_train_random)
    tgt_train_rnd = tgt_train_rnd[:src_data.shape[0]]
    tgt_train_dataset = SeqDataset(tgt_train_rnd)

    if dataset_name:
        path = os.path.join(cache_dir, dataset_name)
        if dataset_name not in os.listdir(cache_dir):
            os.mkdir(path)
        torch.save(src_train_dataset, os.path.join(path, 'src_train_dataset'))
        torch.save(tgt_train_dataset, os.path.join(path, 'tgt_train_dataset'))
        torch.save(src_test_dataset, os.path.join(path, 'src_test_dataset'))

    return src_train_dataset, tgt_train_dataset, src_test_dataset


def get_test_dataset(target_pos: str, target_random: str, dataset_name=None, cache_dir=None,
                     trim_random=True):
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    if dataset_name:
        if dataset_name in os.listdir(cache_dir):
            path = os.path.join(cache_dir, dataset_name)
            tgt_test_dataset = torch.load(os.path.join(path, 'tgt_test_dataset'))
            return tgt_test_dataset

    tgt_pos = read_fasta(target_pos)
    tgt_random = read_fasta(target_random)
    if trim_random:
        tgt_random = tgt_random[:tgt_pos.shape[0]]
    src_data = np.concatenate([tgt_pos, tgt_random], axis=0)
    src_labels = np.concatenate([
        np.ones(tgt_pos.shape[0]),
        np.zeros(tgt_random.shape[0])
    ], axis=0)

    tgt_test_dataset = SeqDataset(src_data, src_labels)

    if dataset_name:
        path = os.path.join(cache_dir, dataset_name)
        if dataset_name not in os.listdir(cache_dir):
            os.mkdir(path)
        torch.save(tgt_test_dataset, os.path.join(path, 'tgt_test_dataset'))

    return tgt_test_dataset


def validate(val_loader, model, args, device, calc_auc=False) -> float:
    batch_time = AverageMeter('Time', ':6.3f')
    losses = AverageMeter('Loss', ':.4e')
    top1 = AverageMeter('Acc@1', ':6.2f')
    progress = ProgressMeter(
        len(val_loader),
        [batch_time, losses, top1],
        prefix='Test: ')

    y_true = []
    y_preds = []

    # switch to evaluate mode
    model.eval()
    if args.per_class_eval:
        confmat = ConfusionMatrix(len(args.class_names))
    else:
        confmat = None

    with torch.no_grad():
        end = time.time()
        for i, data in enumerate(val_loader):
            images, target = data[:2]
            images = images.to(device)
            target = target.to(device)

            # compute output
            output = model(images)
            loss = F.cross_entropy(output, target)

            if calc_auc:
                y_true.append(target)
                y_preds.append(F.softmax(output))

            # measure accuracy and record loss
            acc1, = accuracy(output, target, topk=(1,))
            if confmat:
                confmat.update(target, output.argmax(1))
            losses.update(loss.item(), images.size(0))
            top1.update(acc1.item(), images.size(0))

            # measure elapsed time
            batch_time.update(time.time() - end)
            end = time.time()

            if i % args.print_freq == 0:
                progress.display(i)

        print(' * Acc@1 {top1.avg:.3f}'.format(top1=top1))
        if confmat:
            print(confmat.format(args.class_names))

    if calc_auc:
        y_preds = torch.cat(y_preds).cpu().numpy()[:, 1]
        y_true = torch.cat(y_true).cpu().numpy()
        precision, recall, thresholds = precision_recall_curve(y_true, y_preds)
        pr_auc = auc(recall, precision)
        print(f'PR AUC {pr_auc * 100:.3f}')

        fpr, tpr, thresholds = roc_curve(y_true, y_preds)
        roc_auc = auc(fpr, tpr)
        print(f'ROC AUC {roc_auc * 100:.3f}')

    return top1.avg


def empirical_risk_minimization(train_source_iter, model, optimizer, lr_scheduler, epoch, args, device):
    batch_time = AverageMeter('Time', ':3.1f')
    data_time = AverageMeter('Data', ':3.1f')
    losses = AverageMeter('Loss', ':3.2f')
    cls_accs = AverageMeter('Cls Acc', ':3.1f')

    progress = ProgressMeter(
        args.iters_per_epoch,
        [batch_time, data_time, losses, cls_accs],
        prefix="Epoch: [{}]".format(epoch))

    # switch to train mode
    model.train()

    end = time.time()
    for i in range(args.iters_per_epoch):
        x_s, labels_s = next(train_source_iter)[:2]
        x_s = x_s.to(device)
        labels_s = labels_s.to(device)

        # measure data loading time
        data_time.update(time.time() - end)

        # compute output
        y_s, f_s = model(x_s)

        cls_loss = F.cross_entropy(y_s, labels_s)
        loss = cls_loss

        cls_acc = accuracy(y_s, labels_s)[0]

        losses.update(loss.item(), x_s.size(0))
        cls_accs.update(cls_acc.item(), x_s.size(0))

        # compute gradient and do SGD step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        lr_scheduler.step()

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        if i % args.print_freq == 0:
            progress.display(i)
