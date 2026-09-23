from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = 'C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots'
BASE = 'http://localhost:5173'

TARGETS = [
    ('plan_home_hero_s2', '/'),
    ('plan_standings_s1_zones', '/standings/1'),
    ('plan_standings_s2_active', '/standings/2'),
    ('plan_player_transferred', '/players/9'),
    ('plan_matches', '/matches'),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    page.goto(f'{BASE}/login', timeout=15000)
    page.wait_for_load_state('networkidle', timeout=15000)
    page.locator('input#username').fill('admin')
    page.locator('input#password').fill('admin123')
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(2500)

    for name, path in TARGETS:
        page.goto(f'{BASE}{path}', timeout=15000)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(1500)
        page.screenshot(path=f'{SCREENSHOTS_DIR}/{name}.png', full_page=True)
        print(name)

    browser.close()
print('done')
