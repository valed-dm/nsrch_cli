import json
from pathlib import Path

from bs4 import BeautifulSoup

from src.core.logging_setup import log


def extract_captcha_secrets(html_content: str) -> dict:
    """Uses BeautifulSoup to extract hard technical data from the CAPTCHA page."""
    soup = BeautifulSoup(html_content, "lxml")
    secrets = {
        "form_action_url": None,
        "hidden_inputs": {},
        "site_key": None,
        "instruction_text": None,
    }

    # Find the main form and its submission URL
    form = soup.find("form")
    if form:
        secrets["form_action_url"] = form.get("action")

    # Extract all hidden input fields, which are crucial
    for input_tag in soup.find_all("input", {"type": "hidden"}):
        name = input_tag.get("name")
        value = input_tag.get("value")
        if name:
            secrets["hidden_inputs"][name] = value

    # Try to find a standard reCAPTCHA-style sitekey
    captcha_div = soup.find("div", {"data-sitekey": True})
    if captcha_div:
        secrets["site_key"] = captcha_div["data-sitekey"]

    return secrets

def preprocess_html_for_ai(html_content: str) -> str:
    """
    Surgically removes all noise (scripts, styles, etc.) from the HTML,
    leaving only the core structural and visible elements for the AI to analyze.
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # Find and completely remove all script, style, svg, and other non-content tags
    tags_to_remove = ["script", "style", "svg", "header", "footer", "nav", "aside"]
    for element in soup(tags_to_remove):
        element.decompose() # This removes the tag and all its children

    # Return the cleaned HTML as a string
    return str(soup)

async def analyze_file(file_path: Path) -> dict:
    """Performs a full analysis on a single CAPTCHA file using pre-processing."""
    log.info(f"Analyzing {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    # --- 1. PRE-PROCESSING STEP ---
    log.info(f"Original HTML size: {len(html)} characters.")
    cleaned_html = preprocess_html_for_ai(html)
    log.info(f"Cleaned HTML size for AI: {len(cleaned_html)} characters.")

    # (The deterministic extraction can still run on the original HTML if needed)
    technical_data = extract_captcha_secrets(html)

    # --- 2. AI-powered analysis on the CLEANED HTML ---
    from src.ai.manager import ai_manager

    ai_summary = "AI analysis skipped (manager not available)."
    if ai_manager.is_available():
        system_prompt = ("You are a web security analyst."
                         " Based on the provided CLEANED HTML from a CAPTCHA page,"
                         " provide a short, one-sentence summary of what the user"
                         " needs to do to solve it (e.g., "
                         "'Click the checkbox and then solve a 3x3 image grid challenge.')."
                         )

        # We now send the much smaller, focused HTML to the AI.
        # No more blind truncation is needed.
        response = ai_manager.get_text_completion(
            system_prompt=system_prompt, user_prompt=cleaned_html
        )
        ai_summary = (
            response.get("response", "AI analysis failed.").strip().replace('"', "")
        )

    # --- 3. Combine knowledge ---
    knowledge = {
        "filename": file_path.name,
        "form_action_url": technical_data.get("form_action_url"),
        "hidden_inputs": json.dumps(technical_data.get("hidden_inputs")),
        "site_key": technical_data.get("site_key"),
        "ai_summary": ai_summary,
    }
    return knowledge
