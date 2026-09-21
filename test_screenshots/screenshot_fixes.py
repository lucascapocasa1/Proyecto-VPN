from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = 'C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    
    page.goto('http://localhost:5173/login', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.locator('input#username').fill('admin')
    page.locator('input#password').fill('admin123')
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(3000)
    
    page.goto('http://localhost:5173/standings/1', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/fix_01_standings.png', full_page=True)
    print('Standings fix screenshot taken')
    
    page.goto('http://localhost:5173/statistics', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(3000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/fix_02_statistics.png', full_page=True)
    print('Statistics fix screenshot taken')
    
    page.goto('http://localhost:5173/players/1', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(3000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/fix_03_player_profile.png', full_page=True)
    print('Player profile fix screenshot taken')
    
    browser.close()
