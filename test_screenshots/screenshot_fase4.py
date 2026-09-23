import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = "C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots"
BASE = "http://localhost:5173"
API = "http://localhost:8000"


def api_get(path):
    with urllib.request.urlopen(API + path) as r:
        return json.loads(r.read().decode())


divs = api_get("/api/divisions/?season=1")["results"]
seg = next(d for d in divs if "Segunda" in d["name"])
titles = api_get("/api/club-titles/")["results"]
club_id = titles[0]["club"] if titles else 2
print(f"segunda division id={seg['id']} title club={club_id}")

TARGETS = [
    ("f4_zones_primera_s1", "/standings/1"),
    ("f4_zones_reducido_s1", f"/standings/1/{seg['id']}"),
    ("f4_zones_s2", "/standings/2"),
    ("f4_transfers", "/transfers"),
    ("f4_seasons_edit", "/seasons"),
    ("f4_club_titles", f"/clubs/{club_id}"),
    ("f4_player_profile", "/players/9"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    page.goto(f"{BASE}/login", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.locator("input#username").fill("admin")
    page.locator("input#password").fill("admin123")
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2500)

    for name, path in TARGETS:
        page.goto(f"{BASE}{path}", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(1200)
        page.screenshot(path=f"{SCREENSHOTS_DIR}/{name}.png", full_page=True)
        print(name)

    # match detail with edit panel
    page.goto(f"{BASE}/matches", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(1200)
    page.locator("a.match-card").first.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SCREENSHOTS_DIR}/f4_match_detail_edit.png", full_page=True)
    print("f4_match_detail_edit", page.url)

    # player edit form open
    page.goto(f"{BASE}/players/9", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(1200)
    edit_btn = page.locator("button:has-text('Editar')").first
    if edit_btn.count() > 0:
        edit_btn.click()
        page.wait_for_timeout(800)
    page.screenshot(path=f"{SCREENSHOTS_DIR}/f4_player_edit.png", full_page=True)
    print("f4_player_edit")

    browser.close()
print("done")
