"""Render the 3 Lemo-Opuscar 1920x804 PNG plates for Act 1 via Playwright Chromium."""
import os
from playwright.sync_api import sync_playwright

LEMO_DIR = os.path.dirname(os.path.abspath(__file__))
PLATES = [
    ('beat06_crt.html', 'beat06_crt.png'),
    ('beat09_blueprint.html', 'beat09_blueprint.png'),
    ('beat11_woodcut.html', 'beat11_woodcut.png'),
]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist']
    )
    page = browser.new_page(viewport={'width': 1920, 'height': 804}, device_scale_factor=1)
    for html_name, png_name in PLATES:
        url = 'file://' + os.path.join(LEMO_DIR, html_name)
        out_path = os.path.join(LEMO_DIR, png_name)
        page.goto(url, wait_until='load')
        page.wait_for_timeout(150)
        page.screenshot(path=out_path, type='png')
        print(f"Rendered {out_path}")
    browser.close()
