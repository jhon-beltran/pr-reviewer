"""Stage 2: ask Claude for a structured code review and validate it."""

import anthropic
from dotenv import load_dotenv
from schemas import ReviewResult

load_dotenv()
client = anthropic.Anthropic()

# A small diff with an intentional SQL injection, so the model has something to find.
SAMPLE_DIFF = """
--- a/app/users.py
+++ b/app/users.py
@@ -10,4 +10,5 @@ def get_user(db, user_id):
-    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
"""

# The "form" the model must fill in. The schema is generated from our Pydantic
# model, so there is a single source of truth for the data contract.
REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit the final structured code review for the diff.",
    "input_schema": ReviewResult.model_json_schema(),
}

SYSTEM_PROMPT = (
    "You are a senior software engineer reviewing a pull request. "
    "Only report real problems you can point to in the diff. "
    "Do not invent issues to fill the list. "
    # We can no longer force the tool, so we ask for it explicitly.
    "You MUST deliver your review by calling the submit_review tool. "
    "Never answer with plain text."
)


def review_diff(diff: str) -> ReviewResult:
    """Send a diff to Claude and return a validated review."""
    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        tools=[REVIEW_TOOL],
        # "auto" lets the model decide. Our prompt asks it to use the tool,
        # and we verify below that it actually did.
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": f"Review this diff: \n\n{diff}"}],
    )

    # A truncated answer would produce incomplete data, so fail loudly.
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Response was truncated; increase max_tokens.")

    # Look for the tool call. With "auto", it may be missing.
    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise RuntimeError(
            f"Model did not call submit_review. stop_reason={response.stop_reason}"
        )

    # The guard: raises ValidationError if the data breaks the contract.
    return ReviewResult.model_validate(tool_block.input)


if __name__ == "__main__":
    result = review_diff(SAMPLE_DIFF)
    print(f"Summary: {result.summary}\n")
    for comment in result.comments:
        print(
            f"[{comment.severity.upper()}] {comment.file}:{comment.line} ({comment.category})"
        )
        print(f"  {comment.message}")
        if comment.suggestion:
            print(f"  Fix: {comment.suggestion}")
