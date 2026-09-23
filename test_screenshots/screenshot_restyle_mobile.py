from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = 'C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 375, 'height': 812})

    page.goto('http://localhost:5173/login', timeout=15000)
    page.wait_for_load_state('networkidle', timeout=15000)
    page.locator('input#username').fill('admin')
    page.locator('input#password').fill('admin123')
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(2500)

    for name, path in [('home', '/'), ('standings', '/standings/1'), ('matches', '/matches')]:
        page.goto(f'http://localhost:5173{path}', timeout=15000)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(1200)
        page.screenshot(path=f'{SCREENSHOTS_DIR}/restyle_mobile_{name}.png', full_page=True)
        print(name)

    browser.close()
print('done')
