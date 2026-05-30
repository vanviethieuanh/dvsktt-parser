import os
import sys

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .exporter import export_to_json
from .parser import parse_document, split_pages


def main():
    console = Console()
    console.print("[bold cyan]Đại Việt Sử Ký Toàn Thư Parser[/bold cyan]")

    input_path = "data/chinh-hoa-18.txt"
    output_dir = "output"
    output_path = os.path.join(output_dir, "chinh-hoa-18.json")

    if not os.path.exists(input_path):
        console.print(
            f"[bold red]Error:[/bold red] Input file '{input_path}' not found!"
        )
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Read raw text
        task1 = progress.add_task(description="Reading source file...", total=None)
        with open(input_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        progress.update(task1, completed=True)

        # Step 2: Split and parse
        task2 = progress.add_task(description="Splitting into pages...", total=None)
        pages_text = split_pages(raw_text)
        progress.update(task2, completed=True)

        # Step 3: Run state machine
        task3 = progress.add_task(
            description=f"Parsing {len(pages_text)} pages...", total=None
        )
        doc = parse_document(pages_text)
        progress.update(task3, completed=True)

        # Step 4: Exporting JSON
        task4 = progress.add_task(description="Exporting to JSON...", total=None)
        export_to_json(doc, output_path)
        progress.update(task4, completed=True)

    console.print(
        f"\n[bold green]Success![/bold green] Parsed document exported to: [yellow]{output_path}[/yellow]"
    )

    # Print some stats
    total_parts = len(doc.parts)
    total_volumes = sum(len(p.volumes) for p in doc.parts)
    total_eras = sum(sum(len(v.eras) for v in p.volumes) for p in doc.parts)
    total_notes = len(doc.notes)

    console.print("\n[bold]Summary Stats:[/bold]")
    console.print(f"  - Parts: {total_parts}")
    console.print(f"  - Volumes: {total_volumes}")
    console.print(f"  - Eras: {total_eras}")
    console.print(f"  - Footnotes: {total_notes}")


if __name__ == "__main__":
    main()
