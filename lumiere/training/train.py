from dataclasses import dataclass
from time import time

import torch
from torch.nn import functional as F
from tqdm import tqdm

from lumiere.persistence.storage_client import disable_tokenizer_parallelism
from lumiere.preprocessing.tokenizer import Tokenizer
from lumiere.utils.data import to_batches


@dataclass
class TrainingState:
    avg_loss: float
    avg_perplexity: float
    num_batches: int
    current_lr: float
    global_step: int
    time_taken: float


def train(
    run,
    model: torch.nn.Module,
    tokenizer: Tokenizer,
    dataset: torch.utils.data.Dataset,
    current_epoch: int,
    global_step: int,
    max_epochs: int,
    batch_size: int,
    context_size: int,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler._LRScheduler,
    gradient_clip_norm: float,
    device: torch.device,
) -> TrainingState:
    """Trains the model on the dataset"""
    total_loss = 0.0
    total_perplexity = 0.0
    num_batches = 0
    epoch_steps = 0

    batches = to_batches(tokenizer, dataset, batch_size, context_size + 1)
    start_time = time()
    with tqdm(batches, desc=f"Epoch {current_epoch}/{max_epochs}", leave=False) as pbar:
        for batch in pbar:
            # Evaluate the model on the current batch.
            x, y = (batch[:, :-1].to(device), batch[:, 1:].to(device))
            logits, _ = model(x)
            batch_loss = F.cross_entropy(
                logits.view(-1, tokenizer.vocab_size), y.reshape(-1)
            )
            batch_perplexity = torch.exp(batch_loss)

            # Update the model weights.
            batch_loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), gradient_clip_norm
            )
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            # Calculate running training stats.
            total_loss += batch_loss.item()
            total_perplexity += batch_perplexity.item()
            num_batches += 1
            epoch_steps += 1
            global_step += 1

            # Update progress bar.
            current_lr = scheduler.get_last_lr()[0]
            pbar.set_postfix(
                {
                    "loss": f"{batch_loss:.4f}",
                    "perplexity": f"{batch_perplexity:.4f}",
                    "lr": f"{current_lr:.2e}",
                    "grad_norm": f"{grad_norm:.2f}",
                    "epoch_steps": epoch_steps,
                }
            )

            if run is not None and global_step % 50 == 0:
                with disable_tokenizer_parallelism():
                    run.log(
                        {
                            "train/loss": batch_loss.item(),
                            "train/perplexity": batch_perplexity.item(),
                            "train/lr": current_lr,
                            "train/grad_norm": grad_norm,
                        }
                    )

    end_time = time()
    time_taken = end_time - start_time

    return TrainingState(
        avg_loss=total_loss / num_batches,
        avg_perplexity=total_perplexity / num_batches,
        num_batches=num_batches,
        current_lr=current_lr,
        global_step=global_step,
        time_taken=time_taken,
    )
