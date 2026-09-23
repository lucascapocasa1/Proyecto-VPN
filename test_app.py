from playwright.sync_api import sync_playwright
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCREENSHOTS_DIR = "C:/Users/Capocasa/Desktop/PROYECTO VPN/test_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

errors = []
console_errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(f"[{msg.type}] {msg.text}")

    def on_page_error(err):
        console_errors.append(f"[PAGE ERROR] {err}")

    page.on("console", on_console)
    page.on("pageerror", on_page_error)

    print("=== Test 1: Home page ===")
    try:
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.screenshot(path=f"{SCREENSHOTS_DIR}/01_home.png", full_page=True)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
    except Exception as e:
        errors.append(f"Home page failed: {e}")
        print(f"  ERROR: {e}")

    print("\n=== Test 2: Login page ===")
    console_errors.clear()
    try:
        page.goto("http://localhost:5173/login", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.screenshot(path=f"{SCREENSHOTS_DIR}/02_login.png", full_page=True)
        username_input = page.locator("input[name='username'], input[type='text'], input[placeholder*='user'], input[placeholder*='usuario']")
        password_input = page.locator("input[name='password'], input[type='password']")
        submit_btn = page.locator("button[type='submit'], button:has-text('Login'), button:has-text('Iniciar'), button:has-text('Iniciar sesion'), button:has-text('Entrar')")
        print(f"  Username input: {username_input.count()} found")
        print(f"  Password input: {password_input.count()} found")
        print(f"  Submit button: {submit_btn.count()} found")
        if username_input.count() == 0:
            errors.append("Login page: no username input found")
        if password_input.count() == 0:
            errors.append("Login page: no password input found")
        if submit_btn.count() == 0:
            errors.append("Login page: no submit button found")
    except Exception as e:
        errors.append(f"Login page failed: {e}")
        print(f"  ERROR: {e}")

    print("\n=== Test 3: Login flow ===")
    try:
        page.goto("http://localhost:5173/login", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        username_input = page.locator("input[name='username'], input[type='text'], input[placeholder*='user'], input[placeholder*='usuario']").first
        password_input = page.locator("input[name='password'], input[type='password']").first
        submit_btn = page.locator("button[type='submit'], button:has-text('Login'), button:has-text('Iniciar'), button:has-text('Iniciar sesion'), button:has-text('Entrar')").first
        username_input.fill("admin")
        password_input.fill("admin123")
        page.screenshot(path=f"{SCREENSHOTS_DIR}/03_login_filled.png", full_page=True)
        submit_btn.click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.screenshot(path=f"{SCREENSHOTS_DIR}/04_after_login.png", full_page=True)
        print(f"  URL after login: {page.url}")
        if "/login" in page.url:
            errors.append("Login failed - still on login page")
        else:
            print("  Login successful!")
    except Exception as e:
        errors.append(f"Login flow failed: {e}")
        print(f"  ERROR: {e}")

    print("\n=== Test 4: Navigation ===")
    pages_to_test = [
        ("/", "Home"), ("/countries", "Countries"), ("/leagues", "Leagues"),
        ("/seasons", "Seasons"), ("/standings", "Standings"), ("/clubs", "Clubs"),
        ("/players", "Players"), ("/matches", "Matches"), ("/statistics", "Statistics"),
        ("/transfers", "Transfers"),
    ]
    for path, name in pages_to_test:
        console_errors.clear()
        try:
            page.goto(f"http://localhost:5173{path}", timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/05_{name.lower()}.png", full_page=True)
            print(f"  {name}: OK")
            if console_errors:
                for err in console_errors:
                    print(f"    Console: {err}")
                    errors.append(f"{name}: {err}")
        except Exception as e:
            errors.append(f"{name} failed: {e}")
            print(f"  {name}: ERROR - {e}")

    print("\n=== Test 5: API health ===")
    try:
        resp = page.goto("http://localhost:8000/api/health/", timeout=10000)
        api_content = page.locator("body").text_content()
        print(f"  Health: {api_content[:200]}")
    except Exception as e:
        errors.append(f"API health failed: {e}")
        print(f"  ERROR: {e}")

    print("\n=== Test 5b: Match detail page ===")
    console_errors.clear()
    try:
        page.goto("http://localhost:5173/matches", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        cards = page.locator("a.match-card")
        count = cards.count()
        print(f"  Match cards: {count}")
        if count == 0:
            errors.append("Match detail: no match cards found")
        else:
            cards.first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(1000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/06_match_detail.png", full_page=True)
            print(f"  Detail URL: {page.url}")
            if "/matches/" not in page.url:
                errors.append("Match detail navigation failed")
            if console_errors:
                for err in console_errors:
                    print(f"    Console: {err}")
                    errors.append(f"MatchDetail: {err}")
    except Exception as e:
        errors.append(f"Match detail failed: {e}")
        print(f"  ERROR: {e}")

    print("\n=== Test 6: Nav links ===")
    try:
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        nav_links = page.locator("nav a, header a")
        link_count = nav_links.count()
        print(f"  Found {link_count} nav links")
        for i in range(min(link_count, 15)):
            href = nav_links.nth(i).get_attribute("href")
            text = nav_links.nth(i).text_content()
            print(f"    [{i}] {text.strip()[:30]} -> {href}")
    except Exception as e:
        errors.append(f"Nav check failed: {e}")
        print(f"  ERROR: {e}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if errors:
        print(f"\n{len(errors)} ERRORS FOUND:")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
    else:
        print("\nNo errors found")

    browser.close()
