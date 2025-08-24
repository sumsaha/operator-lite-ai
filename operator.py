import asyncio
import logging
import os
import time
import yaml
import random
from playwright.async_api import async_playwright
from openai import OpenAI, RateLimitError, APIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("operator.log"),
        logging.StreamHandler()
    ]
)

# Init OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper: OpenAI with retries + fallback ---
def call_openai_with_fallback(prompt: str, retries: int = 3, backoff: float = 1.5):
    model_primary = "gpt-4o-mini"
    model_fallback = "gpt-3.5-turbo"

    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt}: calling {model_primary}")
            return client.chat.completions.create(
                model=model_primary,
                messages=[{"role": "user", "content": prompt}]
            )
        except (RateLimitError, APIError) as e:
            wait = backoff ** attempt + random.uniform(0, 0.5)
            logging.warning(
                f"[WARN] Error with {model_primary} on attempt {attempt}/{retries}: {e}. "
                f"Retrying in {wait:.2f}s..."
            )
            time.sleep(wait)
    # If all retries fail → fallback
    logging.warning(f"All retries failed for {model_primary}, falling back to {model_fallback}")
    return client.chat.completions.create(
        model=model_fallback,
        messages=[{"role": "user", "content": prompt}]
    )

# --- AI Planner ---
async def plan_with_ai(instruction: str):
    prompt = f"""
    Convert the following instruction into a YAML plan with steps.
    Instruction: {instruction}
    """
    resp = call_openai_with_fallback(prompt)
    plan_text = resp.choices[0].message.content
    filename = f"plan_{int(time.time())}.yml"
    with open(filename, "w") as f:
        f.write(plan_text)
    logging.info(f"YAML plan written to {filename}")
    return filename

# --- Executor ---
async def execute_plan(yaml_file: str):
    with open(yaml_file) as f:
        plan = yaml.safe_load(f)

    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for idx, step in enumerate(plan.get("steps", []), start=1):
            action = step.get("action")
            target = step.get("target")
            value = step.get("value")

            logging.info(f"Step {idx}: {action} {target or ''} {value or ''}")

            try:
                if action == "goto":
                    await page.goto(target)
                elif action == "fill":
                    await page.fill(target, value)
                elif action == "click":
                    await page.click(target)
                elif action == "wait":
                    await page.wait_for_timeout(int(value) * 1000)

                # Save screenshot + DOM
                screenshot_path = os.path.join(logs_dir, f"step_{idx}.png")
                domdump_path = os.path.join(logs_dir, f"step_{idx}.html")
                await page.screenshot(path=screenshot_path)
                html_content = await page.content()
                with open(domdump_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logging.info(f"Saved screenshot {screenshot_path} and DOM {domdump_path}")

            except Exception as e:
                logging.error(f"Error at step {idx}: {e}")

        await browser.close()

# --- Main ---
async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python operator.py 'Your instruction here'")
        return

    instruction = sys.argv[1]
    logging.info(f"Planning for: {instruction}")
    yaml_file = await plan_with_ai(instruction)
    await execute_plan(yaml_file)

if __name__ == "__main__":
    asyncio.run(main())
