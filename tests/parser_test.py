# import json
# from bs4 import BeautifulSoup
#
# # --- CONFIGURATION ---
# TEST_HTML_FILE = (
#     "/Users/dmvaled/KII/nsrch_cli/old_output/test.html"
# )
#
#
# # --- THE NEW DETERMINISTIC PARSING FUNCTION ---
# def parse_with_selectors(html_content: str) -> list[dict]:
#     """
#     Parses the Yandex SERP HTML using precise BeautifulSoup CSS selectors.
#     This is fast, reliable, and does not require an LLM.
#     """
#     soup = BeautifulSoup(html_content, "lxml")
#     results = []
#
#     # Select all list items that are organic search results
#     # The 'div.serp-item' is the main container for each result
#     serp_items = soup.select("div.serp-item")
#
#     print(f"Found {len(serp_items)} potential 'serp-item' blocks.")
#
#     for item in serp_items:
#         # We look for the main link and title structure within each item.
#         # This helps filter out ads or other blocks that might be in a 'serp-item'.
#         link_tag = item.select_one("a.OrganicTitle-Link")
#
#         if link_tag:
#             # Extract the URL from the 'href' attribute of the <a> tag
#             url = link_tag.get("href")
#
#             # The title is in a specific span inside the link
#             title_tag = link_tag.select_one("span.OrganicTitleContentSpan")
#
#             if url and title_tag:
#                 title = title_tag.get_text(separator=' ', strip=True)
#
#                 results.append({"title": title, "url": url})
#
#     return results
#
#
# # --- SCRIPT LOGIC (Updated) ---
# def run_test():
#     print(f"--- Testing DETERMINISTIC PARSING on file '{TEST_HTML_FILE}' ---")
#
#     try:
#         with open(TEST_HTML_FILE, "r", encoding="utf-8") as f:
#             html_content = f.read()
#     except FileNotFoundError:
#         print(
#             (f"ERROR: Test file not found at '{TEST_HTML_FILE}'."
#              f" Please check the path.")
#         )
#         return
#
#     print("Parsing HTML with BeautifulSoup selectors...")
#     parsed_data = parse_with_selectors(html_content)
#
#     print("\n--- PARSED OUTPUT ---")
#     if parsed_data:
#         print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
#         print(f"\nSUCCESS: Determ. parser extracted {len(parsed_data)} results.")
#     else:
#         print(
#             "WARNING: Parser extracted 0 results."
#         )
#
#
# if __name__ == "__main__":
#     run_test()
