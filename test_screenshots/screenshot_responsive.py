from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = 'C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # Mobile viewport
    page = browser.new_page(viewport={'width': 375, 'height': 812})
    
    page.goto('http://localhost:5173/login', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.locator('input#username').fill('admin')
    page.locator('input#password').fill('admin123')
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(3000)
    
    page.screenshot(path=f'{SCREENSHOTS_DIR}/mobile_01_home.png', full_page=True)
    print('Mobile home screenshot taken')
    
    page.goto('http://localhost:5173/standings/1', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/mobile_02_standings.png', full_page=True)
    print('Mobile standings screenshot taken')
    
    page.goto('http://localhost:5173/matches', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/mobile_03_matches.png', full_page=True)
    print('Mobile matches screenshot taken')
    
    page.goto('http://localhost:5173/statistics', timeout=10000)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SCREENSHOTS_DIR}/mobile_04_statistics.png', full_page=True)
    print('Mobile statistics screenshot taken')
    
    # Tablet viewport
    page2 = browser.new_page(viewport={'width': 768, 'height': 1024})
    
    page2.goto('http://localhost:5173/login', timeout=10000)
    page2.wait_for_load_state('networkidle', timeout=10000)
    page2.locator('input#username').fill('admin')
    page2.locator('input#password').fill('admin123')
    page2.locator('button[type="submit"]').click()
    page2.wait_for_timeout(3000)
    
    page2.goto('http://localhost:5173/', timeout=10000)
    page2.wait_for_load_state('networkidle', timeout=10000)
    page2.wait_for_timeout(2000)
    page2.screenshot(path=f'{SCREENSHOTS_DIR}/tablet_01_home.png', full_page=True)
    print('Tablet home screenshot taken')
    
    page2.goto('http://localhost:5173/standings/1', timeout=10000)
    page2.wait_for_load_state('networkidle', timeout=10000)
    page2.wait_for_timeout(2000)
    page2.screenshot(path=f'{SCREENSHOTS_DIR}/tablet_02_standings.png', full_page=True)
    print('Tablet standings screenshot taken')
    
    browser.close()
