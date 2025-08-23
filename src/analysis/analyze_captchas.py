from pathlib import Path

import pandas as pd

from src.analysis.html_parser import analyze_file
from src.core.config import OUTPUT_DIR
from src.core.config import settings
from src.core.logging_setup import log


def find_captcha_files() -> list[Path]:
    """Finds all saved CAPTCHA HTML files in the output directory."""
    output_dir = settings.CAPTCHAS_DIR
    log.info(f"Searching for CAPTCHA files in {output_dir}...")
    files = list(output_dir.glob("*.html"))
    log.info(f"Found {len(files)} CAPTCHA files to analyze.")
    return files

import asyncio


async def main():
    captcha_files = find_captcha_files()
    if not captcha_files:
        return

    all_knowledge = []
    for file in captcha_files:
        # We can run these in sequence to not overload the AI
        data = await analyze_file(file)
        all_knowledge.append(data)

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(all_knowledge)

    # Save to our knowledge base CSV
    kb_path = OUTPUT_DIR / "captcha_knowledge_base.csv"
    df.to_csv(kb_path, index=False, encoding="utf-8")
    log.success(f"Captcha analysis complete. Knowledge base saved to {kb_path}")
    print(df.head())  # Print the first few rows


if __name__ == "__main__":
    # Ensure all modules are loaded for settings, etc.

    asyncio.run(main())
