import torch.nn as nn


class HybridModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.out_features = 256
        self.conv = nn.Sequential(
            nn.Conv1d(4, 256, 20),
            nn.ReLU(),
            nn.MaxPool1d(15),
            nn.Dropout(0.5),
        )
        self.rnn = nn.LSTM(256, hidden_size=128, bidirectional=True, batch_first=True)

    def forward(self, x):
        x = x.transpose(2, 1)
        x = self.conv(x)
        x = x.transpose(2, 1)
        output, (h_n, c_n) = self.rnn(x)
        x = h_n.transpose(0, 1)
        return x.reshape(x.shape[0], -1)


def hybrid(*args, **kwargs):
    return HybridModel(*args, **kwargs)
