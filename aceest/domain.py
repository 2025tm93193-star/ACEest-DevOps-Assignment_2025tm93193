"""Fitness program templates preserved from Aceestver-3.2.4.py.

These are illustrative rules/templates from the instructor's code, not an AI
service or personalized health advice.
"""
import random

PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"],
}


def choose_program(goal=None):
    """Return a program category and one of its source-defined templates."""
    if goal is not None and goal not in PROGRAM_TEMPLATES:
        raise ValueError("goal must be Fat Loss, Muscle Gain, or Beginner")
    category = goal if goal is not None else random.choice(list(PROGRAM_TEMPLATES))
    return category, random.choice(PROGRAM_TEMPLATES[category])
