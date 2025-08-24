import os
import sys
import yaml
import asyncio
import datetime
import logging
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

async def capture_debug(page, step_counter, selector=None):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(LOGS_DIR, f"step{step_counter}_{ts}.png")
    html_path = os.path.join(LOGS_DIR, f"step{step_counter}_{ts}.html")

    await page.screenshot(path=screenshot_path)
    try:
        html_content = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"HTML dump saved: {html_path}")
    except Exception as e:
        logging.warning(f"Could not save HTML: {e}")

    if selector:
        try:
            el = await page.query_selector(selector)
            if el:
                box = await el.bounding_box()
                if box:
                    img = Image.open(screenshot_path)
                    draw = ImageDraw.Draw(img)
                    x0, y0 = box["x"], box["y"]
                    x1, y1 = x0 + box["width"], y0 + box["height"]
                    draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
                    img.save(screenshot_path)
                    logging.info(f"Annotated screenshot saved: {screenshot_path}")
        except Exception as e:
            logging.warning(f"Annotation failed: {e}")

async def run_plan(yaml_file):
    logging.info(f"Running plan: {yaml_file}")
    with open(yaml_file, "r") as f:
        plan = yaml.safe_load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        step_counter = 1
        for step in plan:
            action = step.get("action")
            logging.info(f"Step {step_counter}: {step}")
            try:
                if action == "goto":
                    await page.goto(step["url"])
                elif action == "click":
                    await page.click(step["target"])
                elif action == "fill":
                    await page.fill(step["target"], step["value"])
                elif action == "wait":
                    await asyncio.sleep(step.get("seconds", 1))
                else:
                    logging.warning(f"Unknown action: {action}")
                await capture_debug(page, step_counter, step.get("target"))
            except Exception as e:
                logging.error(f"Error step {step_counter}: {e}")
                await capture_debug(page, step_counter)
            step_counter += 1

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runner.py plan.yml")
        sys.exit(1)
    asyncio.run(run_plan(sys.argv[1]))
