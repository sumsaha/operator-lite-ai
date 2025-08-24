import sys
import logging
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("planner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

client = OpenAI()

def generate_plan(instruction, filename="generated_plan.yml"):
    logging.info(f"Generating YAML plan for: {instruction}")

    prompt = f"""
    Convert this into YAML automation plan.
    Supported actions: goto, click, fill, wait.
    Instruction: "{instruction}"
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    yaml_text = resp.choices[0].message.content
    with open(filename, "w") as f:
        f.write(yaml_text)

    logging.info(f"Plan saved to {filename}")
    return filename

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python planner.py \"Your instruction here\" [output.yml]")
        sys.exit(1)
    instruction = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else "generated_plan.yml"
    generate_plan(instruction, outfile)
