import re
import json
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

HOME_URL = "https://apps.health.ny.gov/professionals/home_care/registry/home.action"

REGISTRY_INPUT_SEL = "#registry_number"
SEARCH_BTN_SEL = "#submit_number_search"

RESULT_NAME_BTN_SEL = "button.linkbutton[name^='resinums[']"
EMPLOYMENT_BTN_SEL = "button#empl[name='action:employment']"

def _clean(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def _parse_all_employment_history(html: str) -> List[Dict[str, str]]:
    """
    Returns ALL rows in Employment History as:
      [{"agency": "...", "startDate": "..."}, ...]
    """
    soup = BeautifulSoup(html, "lxml")

    table = soup.select_one("table.light_table.profile_table")
    if not table:
        return []

    rows = table.select("tbody tr")
    if not rows:
        return []

    out: List[Dict[str, str]] = []

    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        agency_td = tds[0]
        from_td = tds[1]
        # to_td = tds[2]  # available if you ever want it

        start_date = _clean(from_td.get_text(" ", strip=True))

        # Agency name = first line in <address>
        addr = agency_td.find("address")
        if addr:
            addr_text = addr.get_text("\n", strip=True)
            agency_name = _clean(addr_text.split("\n")[0]) if addr_text else ""
        else:
            agency_name = _clean(agency_td.get_text(" ", strip=True))

        out.append({
            "agency": agency_name,
            "startDate": start_date
        })

    return out
def lookup_current_employment(registry_number: str, headless: bool = True) -> List[Dict[str, str]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(30000)

        # 1) Home page
        page.goto(HOME_URL, wait_until="domcontentloaded")
        page.locator(REGISTRY_INPUT_SEL).fill(registry_number)
        page.locator(SEARCH_BTN_SEL).click()

        # 2) Search results page
        page.wait_for_url(re.compile(r".*/searchworker\.action.*"), timeout=30000)
        page.wait_for_load_state("domcontentloaded")

        # Click caregiver name button (exact)
        btn = page.locator(RESULT_NAME_BTN_SEL)
        if btn.count() == 0:
            browser.close()
            return []
        btn.first.click()

        # 3) Profile page
        page.wait_for_url(re.compile(r".*/worker\.action.*"), timeout=30000)
        page.wait_for_load_state("domcontentloaded")

        # Click Employment History (exact)
        empl = page.locator(EMPLOYMENT_BTN_SEL)
        if empl.count() == 0:
            browser.close()
            return []
        empl.click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(200)

        html = page.content()
        browser.close()

    return _parse_all_employment_history(html)

