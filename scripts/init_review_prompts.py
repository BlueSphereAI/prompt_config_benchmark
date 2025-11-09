#!/usr/bin/env python3
"""Initialize review prompts from JSON files into the database."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_benchmark.storage import ResultStorage
from prompt_benchmark.models import ReviewPrompt
import os


def load_review_prompts():
    """Load review prompts from data/review_prompts into database."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Path to review prompts
    prompts_dir = Path("data/review_prompts")

    if not prompts_dir.exists():
        print(f"❌ Directory not found: {prompts_dir}")
        return

    # Load all JSON files
    for json_file in prompts_dir.glob("*.json"):
        print(f"Loading {json_file.name}...")

        with open(json_file) as f:
            data = json.load(f)

        # Create ReviewPrompt model
        review_prompt = ReviewPrompt(
            prompt_id=json_file.stem,  # Use filename as ID
            name=data["name"],
            description=data.get("description", ""),
            template=data["template"],
            system_prompt=data.get("system_prompt"),
            criteria=data["criteria"],
            default_model=data["default_model"],
            created_by="system",
            is_active=True
        )

        # Save or update in database
        try:
            storage.save_review_prompt(review_prompt)
            print(f"✓ Saved: {review_prompt.name}")
        except Exception:
            # Already exists, update it
            from prompt_benchmark.storage import SQLSession, DBReviewPrompt
            with SQLSession(storage.engine) as session:
                db_prompt = session.query(DBReviewPrompt).filter(
                    DBReviewPrompt.prompt_id == review_prompt.prompt_id
                ).first()

                if db_prompt:
                    db_prompt.name = review_prompt.name
                    db_prompt.description = review_prompt.description
                    db_prompt.template = review_prompt.template
                    db_prompt.system_prompt = review_prompt.system_prompt
                    db_prompt.criteria_json = json.dumps(review_prompt.criteria)
                    db_prompt.default_model = review_prompt.default_model
                    db_prompt.updated_at = review_prompt.created_at
                    session.commit()
                    print(f"✓ Updated: {review_prompt.name}")

    print(f"\n✅ Loaded {len(list(prompts_dir.glob('*.json')))} review prompts")

    # List all prompts in database
    prompts = storage.get_all_review_prompts(active_only=False)
    print(f"\nTotal prompts in database: {len(prompts)}")
    for prompt in prompts:
        status = "✓" if prompt.is_active else "✗"
        print(f"  {status} {prompt.name} ({prompt.prompt_id})")


if __name__ == "__main__":
    load_review_prompts()
