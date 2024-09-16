from typing import List

from beancount.parser.printer import format_entry
from rich import box
from rich.console import Console
from rich.panel import Panel


class UIService:
    @staticmethod
    def display_transaction(
        tx, top_labels: List[str], top_probs: List[float], chatgpt_prediction: str
    ):
        console = Console()
        console.clear()

        tx_panel = Panel(
            format_entry(tx),
            title="Transaction",
            width=80,
            expand=False,
            border_style="cyan",
            box=box.ROUNDED,
        )

        predictions_content = ["Top 3 predictions:"]
        for i, (label, prob) in enumerate(zip(top_labels, top_probs), 1):
            predictions_content.append(
                f"[bold cyan]{i}.[/] [cyan]{label}[/] ({prob:.2f})"
            )
        predictions_content.append(
            f"[bold cyan]4.[/] ChatGPT: [cyan]{chatgpt_prediction}[/]"
        )

        pred_panel = Panel(
            "\n".join(predictions_content),
            title="Predictions",
            width=80,
            expand=False,
            border_style="magenta",
            box=box.ROUNDED,
        )

        console.print(tx_panel)
        console.print(pred_panel)
