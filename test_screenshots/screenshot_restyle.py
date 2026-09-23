from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = 'C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots'

PAGES = [
    ('login', '/login', False),
    ('home', '/', True),
    ('standings', '/standings/1', True),
    ('clubs', '/clubs', True),
    ('players', '/players', True),
    ('matches', '/matches', True),
    ('statistics', '/statistics', True),
    ('club_profile', '/clubs/1', True),
    ('player_profile', '/players/1', True),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    page.goto('http://localhost:5173/login', timeout=15000)
    page.wait_for_load_state('networkidle', timeout=15000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/restyle_00_login.png', full_page=True)
    print('login')

    page.locator('input#username').fill('admin')
    page.locator('input#password').fill('admin123')
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(2500)

    for name, path, auth in PAGES:
        page.goto(f'http://localhost:5173{path}', timeout=15000)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(1500)
        page.screenshot(path=f'{SCREENSHOTS_DIR}/restyle_{name}.png', full_page=True)
        print(name)

    browser.close()
print('done')
