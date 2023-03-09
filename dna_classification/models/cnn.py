import torch.nn as nn


class CnnModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.out_features = 256
        self.conv = nn.Sequential(
            nn.Conv1d(4, 64, 3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64, 128, 3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Conv1d(128, 256, 3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, x):
        x = x.transpose(2, 1)
        x = self.conv(x)[:, :, 0]
        return x


def cnn(*args, **kwargs):
    return CnnModel(*args, **kwargs)
