#!/bin/bash
set -e
echo "Generating demo plan..."
python3 planner.py "Go to example.com login and sign in with demo_user" demo_plan.yml
echo "Executing demo plan..."
python3 runner.py demo_plan.yml
