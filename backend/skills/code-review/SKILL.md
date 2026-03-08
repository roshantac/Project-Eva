---
name: code-review
description: Review code for clarity, correctness, and simple improvements. Use when the user asks for a code review, or when they share a file or snippet to review.
---

When performing a code review:

1. **Understand first**: Read the code and summarize what it does in one sentence.
2. **Correctness**: Note any bugs, edge cases, or logic errors.
3. **Clarity**: Suggest renames, extra comments, or small refactors that make intent clearer.
4. **Style and safety**: Mention style issues (e.g. unused imports, type hints) and security-sensitive patterns if relevant.
5. **Keep it scoped**: Prefer a short, actionable list. For large changes, suggest the top 3–5 items.

Format your review as a brief bullet list. If the user provided a file path, you may use read_file to load it before reviewing.
