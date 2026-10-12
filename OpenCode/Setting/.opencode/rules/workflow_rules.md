# Development Workflow Rules

## Core Principles
1. **KI First**: Always review all Knowledge Items before starting any new task.
2. **ProjectLog.md**: Read before work, update immediately after any significant change.
3. **Gate 1 (Pre-Code Checklist)**:
   - Read ProjectLog & KIs.
   - List exact files created/modified/deleted.
   - Propose plan and wait for explicit user approval ("ok", "go", "approved").
   - Define self-verification strategy.
   - ⛔ NEVER code or modify files without explicit approval.
4. **Gate 2 (Post-Code Checklist / Definition of Done)**:
   - Build/run/syntax check PASS.
   - Real flow verified.
   - Regression checked.
   - Edge cases investigated (empty, null, unicode, negative, timeout).
   - Clean debug output and temporary files.
   - Honest truth reporting (no guessing).
   - ProjectLog updated.
5. **No Silent Scope Creep**: Stop and ask if touching outside approved scope.