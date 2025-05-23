import torch
from torch import nn
from prism.embedding import Embedding
from prism.block import TransformerBlock


class Model(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embedding_size: int,
        context_size: int,
        num_heads: int = 12,
        d_key: int = 64,
        d_value: int = 64,
        d_ff: int = 1024,
        num_layers: int = 6,
        dropout: float = 0.1
    ):
        super().__init__()
        self.embedding = Embedding(vocab_size, context_size, embedding_size)
        
        # Create a stack of transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(
                embedding_size=embedding_size,
                num_heads=num_heads,
                d_key=d_key,
                d_value=d_value,
                d_ff=d_ff,
                dropout=dropout
            )
            for _ in range(num_layers)
        ])
        
        self.final_norm = nn.LayerNorm(embedding_size)
        self.linear_out = nn.Linear(embedding_size, vocab_size, bias=True)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Get embeddings
        x = self.embedding(x)
        
        # Pass through each transformer block
        for block in self.blocks:
            x = block(x)
            
        # Apply final normalization and linear output layer
        x = self.final_norm(x)
        x = self.linear_out(x)
        return x
