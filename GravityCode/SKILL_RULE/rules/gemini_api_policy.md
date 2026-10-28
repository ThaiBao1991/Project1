# Gemini API Safe Usage Policy

1. **Multi-account Key Rotation**: Group keys by account. Rotate keys systematically on request limits.
2. **Quota Error Handling (429 & 503)**:
   - Immediately mark the account with cooldown.
   - Switch to the next available account.
   - Do NOT retry repeatedly with an exhausted key.
3. **Blind Fire Technique**: Fall back instantly in background without blocking or breaking user workflows.