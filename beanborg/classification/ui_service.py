from typing import List

from beancount.parser.printer import format_entry
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


class UIService:
    """UI service for transaction classification."""
    @staticmethod
    def display_transaction(
        tx, top_labels: List[str], top_probs: List[float], chatgpt_prediction: str
    ):
        """Display the transaction with the predictions."""
        console = Console()
        console.clear()

        # Convert the transaction to a string and apply syntax highlighting
        tx_str = format_entry(tx)
        highlighted_tx = Syntax(tx_str, "python", theme="monokai", line_numbers=False)

        tx_panel = Panel(
            highlighted_tx,
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
        if chatgpt_prediction:
            predictions_content.append(
                f"[bold cyan]{len(top_labels) + 1}.[/] ChatGPT: [cyan]{chatgpt_prediction}[/]"
            )

        console.print(tx_panel)

        # Only print the predictions panel if there are predictions to show
        if predictions_content and (len(predictions_content) > 1 or chatgpt_prediction):
            pred_panel = Panel(
                "\n".join(predictions_content),
                title="Predictions",
                width=80,
                expand=False,
                border_style="magenta",
                box=box.ROUNDED,
            )
            console.print(pred_panel)
