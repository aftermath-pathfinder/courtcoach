# Skill: claude-code-security

## When to Apply
Apply this skill at the start of every new project and whenever touching permissions, environment variables, secrets, or external network calls. These are baseline security rules — not optional.

---

## Rule 1: Never Read Credentials or Secrets

Claude Code must never read, print, log, or use the contents of:

```
~/.ssh/**              → SSH private keys
~/.aws/**              → AWS credentials
~/.azure/**            → Azure credentials
~/.kube/**             → Kubernetes configs
~/.gnupg/**            → GPG keys
~/.npmrc               → npm auth tokens
~/.git-credentials     → git credentials
~/.config/gh/**        → GitHub CLI auth
.env                   → project secrets
.env.*                 → all .env variants (e.g. .env.local, .env.production)
```

If a task requires reading one of these paths, stop and ask the user to provide only the specific value needed — never read the file directly.

---

## Rule 2: No Outbound Network Commands

Claude Code must never execute:

```bash
curl *       # data exfiltration risk
wget *       # data exfiltration risk
nc *         # netcat — raw socket access
ssh *        # remote access
```

If a task requires downloading something, present the command to the user and ask them to run it manually.

---

## Rule 3: Never Modify Shell Config Files

Claude Code must never edit:

```
~/.bashrc
~/.zshrc
~/.bash_profile
~/.profile
```

Changes to shell config persist across all sessions and are a common persistence attack vector. If shell config changes are needed, show the user what to add and let them do it.

---

## Rule 4: No Auto-Push to Git

Claude Code must never run `git push` automatically. Always stage, commit, and show a diff — then wait for explicit user approval before pushing.

---

## Rule 5: Secrets Stay in .env — Never in Code

- Never hardcode API keys, tokens, passwords, or credentials anywhere in source code
- Never log secret values — mask them in output (e.g. `HF_API_TOKEN=sk-***`)
- Always read secrets from environment variables via the project's `.env` file
- `.env` is always in `.gitignore` — `.env.example` with placeholder values is what gets committed

---

## Rule 6: MCP Servers Are Opt-In

- Never enable project-level MCP servers automatically when opening an unfamiliar repo
- `enableAllProjectMcpServers` should be `false` in `~/.claude/settings.json`
- Only enable MCP servers you explicitly added yourself

---

## Rule 7: Dependency Security

- Before installing any new package, check it exists on the official registry (npmjs.com or pypi.org) — typosquatting is a real attack vector
- Prefer packages with high download counts, recent maintenance, and no open critical CVEs
- Never install packages suggested by an LLM without verifying the exact package name on the official registry first

---

## Recommended ~/.claude/settings.json

Every developer on this project should have this in their global Claude Code settings. This is a personal machine config — do not commit it to the repo.

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(npm test *)",
      "Bash(npx prettier *)",
      "Bash(npx eslint *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(grep *)",
      "Bash(pytest *)",
      "Bash(pip install *)",
      "Bash(docker-compose *)",
      "Bash(uvicorn *)"
    ],
    "deny": [
      "Read(~/.ssh/**)",
      "Read(~/.gnupg/**)",
      "Read(~/.aws/**)",
      "Read(~/.azure/**)",
      "Read(~/.kube/**)",
      "Read(~/.npmrc)",
      "Read(~/.git-credentials)",
      "Read(~/.config/gh/**)",
      "Edit(~/.bashrc)",
      "Edit(~/.zshrc)",
      "Edit(~/.bash_profile)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(nc *)",
      "Bash(ssh *)",
      "Bash(git push *)",
      "Read(*.env)",
      "Read(.env.*)"
    ]
  },
  "enableAllProjectMcpServers": false
}
```

**To apply this:**
```bash
mkdir -p ~/.claude
# Create or merge into ~/.claude/settings.json
```

Note: `git push` is in the deny list intentionally — Claude stages and commits, you push. This keeps you in control of what leaves your machine.

---

## What This Skill Does NOT Cover

- **Sandbox (`/sandbox`)** — sandbox is an OS-level feature you enable once per machine inside a Claude Code session. Run `/sandbox` and choose Auto-allow mode. This skill can't enforce it automatically.
- **Container isolation** — for running Claude Code against untrusted repos, consider a devcontainer. Out of scope for personal projects but worth knowing about.
- **CVE scanning** — dependency vulnerability scanning (e.g. `npm audit`, `pip-audit`) should be added to CI when you set up GitHub Actions. Add to backlog.
