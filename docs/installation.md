# Installing the skill across hosts

This page covers skill directories, links, and copy mode. Where the discovery log and rules file live is a workflow decision documented in `skills/self-evolution/references/adapters.md`.

## Skill roots

As of 2026-10-28, `.agents/skills/` is the shared project root for Codex, Cursor, OpenCode, and GitHub Copilot. Claude Code is the exception and needs a bridge.

| Host | Project scope | User scope | Reads `.agents/skills`? |
| --- | --- | --- | --- |
| Claude Code | `.claude/skills/<name>/SKILL.md`; nested `.claude/skills`; `.claude/skills` in a `--add-dir` directory; plugins | `~/.claude/skills/` | No |
| OpenAI Codex | `.agents/skills` in the working directory, each parent, and the repository root | `~/.agents/skills/`; `/etc/codex/skills` for admin scope | Yes |
| Cursor | `.agents/skills/`, `.cursor/skills/`; nested directories are scoped to their subtree | `~/.agents/skills/`, `~/.cursor/skills/`; compatibility reads from `~/.claude/skills/` and `~/.codex/skills/` | Yes |
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | Yes |
| GitHub Copilot (cloud, CLI, app) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/`, `~/.agents/skills/` | Yes |
| Copilot in VS Code | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | Yes |

Notes:

- Claude Code does not read `.agents/skills` as of this date. It loads `.claude/skills` from a directory passed with `--add-dir`, and supports a skill-folder entry that is a symlink to a directory elsewhere.
- Codex follows symlinked skill folders and scans parent directories up to the repository root.
- Cursor, OpenCode, and Copilot document the paths above but do not document symlink or junction handling. Verify after setup.
- `gh skill` (GitHub CLI 2.90+, public preview) installs, updates, validates, and publishes skills; `--agent` selects the host directory.

## Canonical layout

```text
.agents/skills/<name>/SKILL.md   # tracked, canonical
AGENTS.md                        # tracked, shared rules
.claude/skills/                  # generated bridge, git-ignored when link-only
```

Windows, PowerShell:

```powershell
$root = git rev-parse --show-toplevel
$store = Join-Path $root ".agents/skills"
$bridge = Join-Path $root ".claude/skills"
New-Item -ItemType Directory -Force $bridge | Out-Null

Get-ChildItem $store -Directory | ForEach-Object {
    $link = Join-Path $bridge $_.Name
    if (-not (Test-Path -LiteralPath $link)) {
        New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
    }
}
```

Linux and macOS:

```bash
root=$(git rev-parse --show-toplevel)
mkdir -p "$root/.claude/skills"
for dir in "$root"/.agents/skills/*/; do
    name=$(basename "$dir")
    [ -e "$root/.claude/skills/$name" ] || \
        ln -s "../../.agents/skills/$name" "$root/.claude/skills/$name"
done
```

Add `.claude/skills/` to `.gitignore` only when it contains links only.

## Symlinks are not junctions

Linux and macOS do not have junctions. They have POSIX symbolic links. A junction is a Windows-only NTFS reparse point; the closest POSIX equivalent is a directory symlink. Do not use the terms interchangeably in setup instructions.

| Property | POSIX symlink (Linux, macOS) | Windows junction | Windows symlink |
| --- | --- | --- | --- |
| Mechanism | Special file containing a path | NTFS reparse point | NTFS reparse point |
| Targets | Files or directories; relative or absolute; any filesystem | Directories only; local volumes only; no mapped network drives | Files or directories; relative or absolute; UNC allowed |
| Privilege | Write permission on the parent directory | None by default | Administrator or Developer Mode |
| Git | Stored as a symlink (mode `120000`) | Treated as a real directory; target contents are indexed | Stored as a symlink when `core.symlinks=true`, otherwise checked out as a text file |
| Node `Dirent` | `isSymbolicLink()` | `isSymbolicLink()` (not `isDirectory()`) | `isSymbolicLink()` |
| Python `pathlib` | `is_symlink()`; `is_dir()` follows | `is_dir()`; `is_symlink()` is false | `is_symlink()` |

Consequences:

- Use `ln -s` on Linux and macOS. Use a junction on Windows only because it avoids the symlink privilege requirement.
- A Git repository that commits a junction commits the target contents, not a link. A repository that commits a symlink commits a link that Windows may check out as text unless `core.symlinks` is enabled.
- A host scanner that filters on directory entries may skip junctions because Node reports them as symlinks. Python-based scanners usually traverse them.

## When to link, when to copy

| Situation | Use | Why |
| --- | --- | --- |
| Local Windows workstation, Claude Code bridge | Per-skill junction | No administrator rights; single source of truth |
| Local macOS or Linux workstation | Per-skill symlink | Native mechanism; Git-portable if committed |
| CI, cloud agents, fresh checkouts | Copy | Links are not reliably preserved or permitted |
| Teammates who clone the repository | Copy, or run the bootstrap script | A junction is local to one machine |
| Skills directory on a network share | Copy, or a symlink with privilege | Junctions cannot target mapped network volumes |
| Directory an agent may archive, clean, or delete | Copy, or keep links out | Some cleanup code traverses reparse points and deletes the target contents |

Copy-based installs: `npx skills add <owner>/<repo> --copy` or `gh skill install <owner>/<repo> <skill> --agent claude-code`.

## Junction safety rules

1. Link one skill at a time, not the whole `.claude/skills` root. A bad entry then costs one skill, not the catalog.
2. Keep junctions out of tracked worktrees. Git indexes the target contents as ordinary files, including targets outside the repository; a fresh clone cannot reproduce that state.
3. Keep junctions out of agent-managed worktrees and cleanup paths. There are reproduced reports of worktree archive and retention cleanup deleting files through a junction target.
4. Junctions are local-volume only. Do not plan a shared store on a mapped network drive.
5. Verify after setup. If the host does not list the skill, switch that skill to copy mode instead of debugging the link.
6. Back up the target before testing any cleanup behavior against it.

## Verify the wiring

- Claude Code: `/skills`; invoke the skill once.
- Codex: `/skills`, or `$skill-name`.
- Cursor: **Customize → Skills**.
- Copilot: the skills UI, or `/skills` where the host exposes it.
- Spec check: `gh skill publish --dry-run` or `skills-ref validate <path>`.

## Sources (retrieved 2026-10-28)

- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code memory and `AGENTS.md`: https://code.claude.com/docs/en/memory
- OpenCode skills: https://opencode.ai/docs/skills/
- Cursor skills: https://cursor.com/docs/skills
- GitHub Copilot skills: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- VS Code agent skills: https://code.visualstudio.com/docs/agent-customization/agent-skills
- Codex skills: https://developers.openai.com/codex/skills
- Agent Skills specification: https://agentskills.io/specification
- Windows junctions: https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions
- Git for Windows symlinks: https://gitforwindows.org/symbolic-links.html
- GitHub CLI `gh skill`: https://cli.github.com/manual/gh_skill
