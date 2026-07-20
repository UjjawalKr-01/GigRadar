"""
pitch.py
Drafts a short, personalized opening pitch for a job post using the Anthropic API.
Requires ANTHROPIC_API_KEY to be set. If it's missing, falls back to a generic template
so the bot still works without it.
"""

import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

FALLBACK_TEMPLATE = (
    "Hi! I saw your post about \"{title_snippet}\" — I can help with this. "
    "I've got experience with similar tasks and can turn it around quickly. "
    "Happy to share more detail or hop on a quick chat if useful."
)


def draft_pitch(post):
    title_snippet = post.get("title", "")[:80]

    if not ANTHROPIC_API_KEY:
        return FALLBACK_TEMPLATE.format(title_snippet=title_snippet)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""You are drafting a short, casual, confident opening message from a freelance developer
replying to this job post. Keep it under 60 words, no fluff, no "I hope this finds you well",
just: acknowledge the specific task, state you can do it, ask one clarifying question if it's genuinely
ambiguous, and invite them to reply. Do not invent specific past projects or credentials.

Post title: {post.get('title','')}
Post body: {post.get('body','')[:800]}

Write only the message, nothing else."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [b.text for b in response.content if b.type == "text"]
        return "\n".join(text_blocks).strip() or FALLBACK_TEMPLATE.format(title_snippet=title_snippet)
    except Exception as e:
        print(f"[pitch] Claude API failed, using fallback: {e}")
        return FALLBACK_TEMPLATE.format(title_snippet=title_snippet)
