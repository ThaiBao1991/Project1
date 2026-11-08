# Shared AI Working Rules

These rules are tool-neutral. Apply them in Codex, Gemini, Claude, and other AI coding tools. Project-local rules override this file when they conflict.

## Before changes

- Read relevant project documentation when it exists, such as `ProjectLog.md`, `PROJECT_MEMORY.md`, `docs/`, and task-specific knowledge files. Do not scan unrelated projects.
- For a non-trivial, multi-file, risky, destructive, or unclear change, present the goal, affected files, approach, risks, and verification plan; wait for explicit approval.
- For a small, reversible, well-scoped fix, proceed without a separate approval gate and report the change clearly.
- Do not materially expand scope without confirmation.

## During changes

- Make the smallest focused change that solves the request.
- Do not delete user files, rewrite history, modify secrets, or perform external actions without explicit approval.
- Create temporary files only when needed. Remove only temporary files created by the agent, after verification.
- Preserve existing project conventions, dependencies, and formatting unless the task asks to change them.

## Verification and reporting

- Run the relevant available test, build, lint, type check, or syntax check.
- Check related call sites and realistic edge cases for a meaningful code change.
- Report only observed results: what was checked, how it was checked, the result, and any verification that could not be performed.
- Remove newly introduced debug output and clearly labelled temporary TODOs before completion.
- Update a project log or memory file only when a significant decision, bug fix, architecture change, or known limitation should persist.

## Text and encoding

- Store text files as UTF-8.
- For Unicode data encoded as Base64 in browser JavaScript, use `TextEncoder` and `TextDecoder`; do not use deprecated `escape` or `unescape` conversions.

```js
const bytesToBinary = (bytes) => {
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return binary;
};

const encodeBase64Utf8 = (value) =>
  btoa(bytesToBinary(new TextEncoder().encode(JSON.stringify(value))));

const decodeBase64Utf8 = (encoded) => {
  const binary = atob(encoded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
};
```
