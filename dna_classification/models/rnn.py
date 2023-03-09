import torch.nn as nn


class RnnModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.out_features = 256
        self.rnn = nn.LSTM(4, hidden_size=128, bidirectional=True, batch_first=True)

    def forward(self, x):
        output, (h_n, c_n) = self.rnn(x)
        x = h_n.transpose(0, 1)
        return x.reshape(x.shape[0], -1)


def rnn(*args, **kwargs):
    return RnnModel(*args, **kwargs)
