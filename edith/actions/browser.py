from typing import Dict, Any
import threading
from playwright.sync_api import sync_playwright
from edith.core.registry import registry
from edith.utils.logger import logger

def _run_browser_search(query: str):
    """Runs playwright in a separate thread so it doesn't block forever if left open."""
    try:
        with sync_playwright() as p:
            # We use chromium as the default. Headless=False so the user can see it.
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Simple heuristic: if it looks like a URL, go there, otherwise Google it
            if "." in query and " " not in query:
                if not query.startswith("http"):
                    query = "https://" + query
                page.goto(query)
            else:
                page.goto(f"https://www.google.com/search?q={query}")
                
            # Keep browser open until the user closes it manually or script exits
            # We wait for the page to be closed
            page.wait_for_event("close", timeout=0)
            browser.close()
    except Exception as e:
        logger.error(f"Playwright error: {e}")

@registry.register("browser_search")
def browser_search(intent_data: Dict[str, Any]) -> str:
    query = intent_data.get("query")
    
    if not query:
        return "I didn't catch what you wanted to search for."

    logger.info(f"Browser search triggered for: {query}")
    
    # Run in background thread to avoid blocking the assistant
    t = threading.Thread(target=_run_browser_search, args=(query,), daemon=True)
    t.start()
    
    return f"Searching for {query}."
