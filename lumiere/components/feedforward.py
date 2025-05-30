import torch
from torch import nn

class FeedForward(nn.Module):
    """Feed-forward network for the transformer block.
    
    Args:
        embedding_size (int): The size of the embedding
        d_ff (int): The size of the feed-forward network
        dropout (float): Dropout probability
    """
    def __init__(self, embedding_size: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear_1 = nn.Linear(embedding_size, d_ff, bias=True)
        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.linear_2 = nn.Linear(d_ff, embedding_size, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.linear_1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear_2(x)
        return x