---
title: "Agent Skill Adapters: Compatibility and Windows Junction Strategy"
subtitle: "A verification of skills/self-evolution/references/adapters.md"
date: 2026-10-28
mode: deep
status: final
---

# Agent Skill Adapters: Compatibility and Windows Junction Strategy

## Executive Summary

The `adapters.md` reference in the self-evolution skill describes a host landscape that no longer exists. It presents agent skill placement as a per-host choice, with Claude Code on `CLAUDE.md`, OpenCode on `AGENTS.md`, Codex on an unspecified convention, Cursor on rules, and Copilot as "host-dependent." Current vendor documentation shows the opposite: a vendor-neutral project root, `.agents/skills/`, is read natively by Codex, Cursor, OpenCode, and GitHub Copilot, and only Claude Code remains outside it [1][3][4][5][6][8]. The instruction-file layer has converged as well: `AGENTS.md` is the shared default across all five hosts, and Claude Code has read it natively since v2.1.277 when no `CLAUDE.md` is present [2][10].

The pessimism has a cost. A document that tells operators to pick one host or keep parallel copies creates the drift it is trying to prevent. The correct default in October 2026 is one canonical store in `.agents/skills/`, one shared `AGENTS.md`, and a single bridge for Claude Code.

Windows directory junctions are a legitimate part of that bridge, but a narrower one than the question assumes. Junctions need no administrator rights and are transparent to most file APIs [11][12][13]. The popular `npx skills` installer already uses them by default to link skills into `~/.claude/skills` [14][19]. But Node-based scanners report a junction as a symbolic link rather than a directory, so any host that filters on `isDirectory()` can silently skip it [14]. More seriously, Git indexes a junction's target contents as ordinary files, including targets outside the repository; a local experiment staged the same file twice through a junction and a real directory, and staged an external file through an out-of-tree junction [18]. Agent cleanup has also deleted junction targets recursively, with one reproduced incident and two corroborating reports [17].

The defensible design is therefore: canonical `.agents/skills/`, `AGENTS.md` as the shared rules file, per-skill junctions (not one top-level junction) only for local Windows Claude Code use, and a copy-based install for CI, cloud, teammates, and any directory an agent may archive or clean. Junctions are an implementation detail of the bridge, not the architecture.

## Introduction

### Scope

This report verifies the factual claims in `skills/self-evolution/references/adapters.md` as published on 2026-10-28 and answers two narrower questions: whether the document is overly pessimistic about cross-host compatibility, and whether Windows directory junctions can improve it. The scope covers five hosts named in the document — Claude Code, OpenCode, OpenAI Codex, Cursor, and GitHub Copilot, including its VS Code surface — plus the Windows filesystem and Git behavior that determines whether junctions are safe.

Out of scope: cloud-only agent platforms not mentioned in the document, the internal design of each host's skill loader, macOS/Linux symlink behavior beyond comparison, and a security audit of third-party skills.

### Method

The research followed the deep-research pipeline: scope, plan, parallel retrieval from vendor documentation, triangulation against issue trackers and independent reports, outline refinement, synthesis, critique, and packaging. Vendor documentation supplied the authoritative path lists [1]–[8]. The Agent Skills specification and the `AGENTS.md` project supplied the format-level contract [9][10]. Microsoft and Git for Windows documentation supplied filesystem semantics [11][12][13]. GitHub issue trackers supplied field reports where vendor documentation is silent or contradicted [14]–[18]. Where possible, claims were checked by direct experiment on the research machine: junction creation, runtime classification, Git staging, and deletion behavior. The experiment log is in the methodology appendix.

### Assumptions

Three assumptions shape the conclusions. First, "compatibility" means that a host discovers a skill placed in a documented location without per-session configuration; a host that requires a flag or a plugin is noted separately. Second, a skill is portable when its directory is discoverable, not when every optional frontmatter field is honored; hosts legitimately differ on invocation controls. Third, the reader is setting up a repository or a single Windows workstation, not a managed enterprise fleet; managed settings can override discovery and are called out only where relevant.

## Main Analysis

### Finding 1: `.agents/skills` is already the neutral root; Claude Code is the only holdout

The adapter document's first table gives each host a different skill location and implies that supporting several hosts requires several copies. The current documentation contradicts that implication in a specific and useful way: four of the five hosts read the same project directory, `.agents/skills/`.

OpenAI's Codex documentation states that Codex scans `.agents/skills` in the current working directory, in each parent directory up to the repository root, and at the repository root, and also reads `$HOME/.agents/skills` for user scope [8]. Cursor's documentation lists `.agents/skills/` and `.cursor/skills/` as project locations and `~/.agents/skills/` and `~/.cursor/skills/` as user locations, and adds compatibility reads from `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, and `~/.codex/skills/` [4]. OpenCode documents six locations: `.opencode/skills/`, `~/.config/opencode/skills/`, `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, and `~/.agents/skills/` [3]. GitHub Copilot documents project skills in `.github/skills`, `.claude/skills`, or `.agents/skills`, and personal skills in `~/.copilot/skills` or `~/.agents/skills`; VS Code repeats the same project set and adds `~/.claude/skills/` for personal scope [5][6].

Claude Code is the exception. Its documented locations are `.claude/skills/<name>/SKILL.md` for project scope, `~/.claude/skills/` for personal scope, nested `.claude/skills/` directories, a `.claude/skills` inside any directory passed with `--add-dir`, and plugin-provided skills [1]. The same page explicitly notes that a skill folder entry may be a symlink to a directory elsewhere on disk, and that Claude Code loads the skill once even when several locations point at the same target [1]. No `.agents/skills` location appears in the Claude Code list.

The practical consequence is a 4:1 split, not a 1:1:1:1:1 split. A repository that writes its skills once under `.agents/skills/` gets Codex, Cursor, OpenCode, and Copilot for free. Only Claude Code needs a bridge: a per-skill link, a copy, or a plugin. That is a much smaller compatibility problem than the adapter document describes, and it is the single most important correction to make.

The document also mislabels individual rows. It places Cursor's skills under `.cursor/rules/`, which is the rules directory, not the skill directory; modern Cursor documents `.cursor/skills/` and `.agents/skills/`, and describes `.cursor/rules/` as the place for rules [4]. It calls Copilot "host-dependent" when GitHub and Microsoft publish a concrete list [5][6]. It gives Codex "AGENTS.md skill conventions of the host," which is not a path at all; Codex uses `.agents/skills` [8]. These are not stylistic gaps. An operator following the table would create directories that some hosts never scan.

There is one nuance worth preserving rather than flattening: discovery is not invocation. A host may discover a skill and still require the user to enable it, grant permission, or invoke it explicitly. OpenCode, for example, supports permission patterns that can hide or deny a skill [3]. Claude Code supports `disable-model-invocation` and `user-invocable` controls [1]. The adapter document should distinguish "where the file goes" from "whether the host will run it," because conflating the two is how a correctly placed skill gets reported as broken.

### Finding 2: `AGENTS.md` has become the shared instruction file, including for Claude Code

The adapter table assigns `CLAUDE.md` to Claude Code and `AGENTS.md` to OpenCode and Codex, with Cursor on `.cursor/rules/*.mdc` and Copilot on `.github/copilot-instructions.md`. This was accurate enough in early 2025 and is misleading in October 2026.

Claude Code's memory documentation now describes native `AGENTS.md` support. When a repository has an `AGENTS.md` and no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in the working directory or any directory above it, Claude reads the `AGENTS.md` files directly [2]. The behavior requires Claude Code v2.1.277 or later; the documentation notes that some sessions on versions before v2.1.281, such as Bedrock sessions or sessions with telemetry disabled, could not load `AGENTS.md` and should be updated [2]. A setting, exposed in `/config` as **Project instructions**, can force four modes: `claude-md-or-agents-md` (the default), `claude-md-and-agents-md`, `claude-md`, and `managed-only` [2].

The precedence rule is the trap. If a `CLAUDE.md` exists anywhere in the working directory or above it, Claude reads the `CLAUDE.md` files and ignores `AGENTS.md` unless the setting is changed [2]. A repository that adds `AGENTS.md` for Codex and later inherits a stale `CLAUDE.md` from an earlier experiment will silently stop honoring the shared file. The documentation recommends either deleting the redundant `CLAUDE.md`, importing `AGENTS.md` with `@AGENTS.md`, or setting `claude-md-and-agents-md` [2]. The import is the most portable choice because it also works in sessions where native `AGENTS.md` loading is unavailable.

The symlink shortcut is less portable than it looks, and this matters for the junction discussion. Anthropic's own guidance warns that on Windows a `CLAUDE.md` symlink to `AGENTS.md` requires Administrator privileges or Developer Mode, and that Git checks out a committed symlink as a plain text file unless `core.symlinks` is enabled, leaving a one-line `CLAUDE.md` in place of the instructions [2]. The recommended workaround is the `@AGENTS.md` import, not a link [2]. For a cross-platform repository, that is the right default.

Cursor, Copilot, and OpenCode all consume `AGENTS.md` as well. The `AGENTS.md` project lists Codex, Jules, Factory, Aider, goose, OpenCode, Zed, Warp, VS Code, Devin, UiPath, Junie, Amp, Cursor, RooCode, Gemini CLI, Kilo Code, Phoenix, Semgrep, GitHub Copilot's coding agent, Ona, Windsurf, and Augment among its supported agents [10]. VS Code's instruction documentation treats `AGENTS.md` as a first-class project instruction format for Copilot and notes that it is a cross-agent format rather than a Codex-specific one [7].

The correct adapter table therefore has one shared row for `AGENTS.md`, one optional row for `CLAUDE.md` when a repository genuinely needs Claude-specific instructions, and host-specific rows only for path-scoped or always-on rules that cannot live in the shared file. That is a smaller table and a more accurate one.

### Finding 3: Junctions are a real Windows bridge, but host support is implicit and uneven

A Windows directory junction is a reparse point that redirects one directory path to another directory on the same computer. Microsoft's documentation permits junctions between directories on different local volumes and explicitly disallows mapped network volumes as targets; hard links are files-only, and junctions cannot point at files [11]. The `mklink /J` command creates one [12]. Linux and macOS have no junction type at all; their equivalent is the POSIX symbolic link, which can target files or directories, cross filesystems, and use relative or absolute paths [23]. Windows also has a true symbolic link (`mklink /D`) that is closer to the POSIX mechanism, but it requires the privilege discussed below [13]. Git for Windows notes that junctions can be created by non-administrator users by default, which is why they are a popular alternative to symbolic links; symbolic links require `SeCreateSymbolicLinkPrivilege`, held by Administrators and guarded by UAC, unless Developer Mode or an explicit policy assignment removes the elevation requirement [13].

That privilege difference is the reason junctions keep appearing in agent tooling. The `npx skills` installer, which supports Claude Code, OpenCode, Codex, Cursor, and dozens of other agents, links each installed skill into the agent's directory with a Windows directory junction, because real symlinks need administrator rights or Developer Mode [14][19]. The installer's own issue tracker describes this as the correct default that preserves a single source of truth, with a `--copy` fallback for environments where links are problematic [20]. In other words, the junction approach is not an exotic workaround; it is the default installation mechanism of the most widely used skills CLI.

Host documentation is less explicit. Claude Code documents that a skill folder entry may be a symlink to a directory elsewhere on disk and that Claude Code reads `SKILL.md` from the target [1]. Codex documents that it "supports symlinked skill folders and follows the symlink target when scanning these locations" [8]. Cursor, OpenCode, and Copilot do not document symlink or junction handling in their skill pages [3][4][5][6]. Silent support is not a contract: it can change in a patch release without a documentation change.

The runtime classification is the technical fault line. On the research machine, Node 18 reported a junction as `isDirectory=false, isSymbolicLink=true`, while Python 3.12 reported the same path as a directory (`is_dir=True`, `is_symlink=False`) and traversed it transparently. This is not a Node bug; it reflects the `Dirent` type for a reparse point. Any scanner written in Node or Bun that keeps only entries where `isDirectory()` is true will drop a junctioned skill folder. The Claude Code issue tracker contains exactly this analysis: a junctioned skill loaded for the model but was missing from a desktop menu scan, with `readdirSync` output showing `isDirectory=false, isSymbolicLink=true` [14]. The reporter later closed the issue after concluding that the desktop menu dropped real-directory skills too and that the behavior was non-deterministic, so the junction was not proven to be the cause in that surface [14]. A separate report described a junctioned skill that appeared in the skill list but failed on first invocation with "Unknown skill" until another tool call refreshed the registry, and was closed as a duplicate of a broader invocation bug [15]. A third report, claiming that a symlinked `~/.claude/skills` root broke discovery, was withdrawn by its author after fully copied directories failed the same way [16].

The honest reading is not "junctions work" or "junctions fail." It is that junctions are transparent enough for some loaders and invisible to others, vendor documentation does not guarantee either behavior, and published bug reports have repeatedly misattributed broader discovery bugs to junctions. An operator should treat a junction as a supported-by-experience mechanism, verify it in each host after setup, and keep a copy fallback for cases where verification fails.

### Finding 4: the real junction risk is repository integrity and destructive cleanup, not discovery

The compatibility question is the smaller half of the junction decision. The larger half is what a junction does to version control and to tools that delete directories.

Git does not treat a Windows junction as a symbolic link. In a controlled experiment, a repository contained a real directory `real/` with `file.txt` and a junction `linked/` pointing at it. `git add .` staged both `linked/file.txt` and `real/file.txt`; `git ls-files` listed both. A second experiment pointed a junction at a directory outside the repository; `git add .` staged `linked/external.txt` from the external target as an ordinary repository file. The repository now contains content that does not exist in its working tree after a fresh clone, because a clone receives a plain directory or no directory at all, not the link. The VS Code issue tracker documents the same class of confusion: a repository with a directory junction does not mark changed files inside the junction as modified without reloading the Git extension [18].

This is not a theoretical purity concern. A skill farm committed through junctions duplicates every skill file in the index, doubles diffs when a skill changes, and can silently import secrets or build artifacts from outside the repository. The correct rule is blunt: never commit a junction farm inside a tracked worktree. If junctions are used, the link directory must be ignored by Git and recreated by a bootstrap script on each clone. The canonical skill content stays in a real directory that Git tracks normally.

The destructive-cleanup risk is more severe. The Codex issue tracker contains a reproduced data-loss report: archiving a Codex-managed Git worktree recursively removed a file from the real directory referenced by a Windows junction inside that worktree. The junction path and the worktree were removed, the real target directory remained, and its contents were deleted [17]. Two later comments corroborate the pattern: one reports automatic worktree retention cleanup emptying a local checkout's `node_modules` and `.venv` through junctions, deleting 270 tracked files that were recoverable from Git; another reports 7,148 files and 224 directories deleted from a shared assets folder through a junction during `archive_worktree`, with NTFS journal records confirming the scope and timing [17]. The common factor is a cleanup implementation that traverses a reparse point instead of unlinking it as a leaf entry.

Not every deletion path is dangerous. In the research experiment, PowerShell 7 `Remove-Item -Recurse`, `cmd /c rmdir`, Node's `fs.rmSync({recursive:true})`, and `git clean -fdx` on an ignored junction each removed the link without deleting the target. That is reassuring for ordinary cleanup, and it is exactly why the Codex incidents matter: the dangerous behavior is implementation-specific, appears in agent-managed worktree cleanup, and is not visible until data is gone.

Two further constraints follow from Microsoft's documentation. Junctions cannot target mapped network volumes, so a shared skills store on a network drive is not an option; a junction to a UNC path is not permitted [11]. Symbolic links can target UNC paths [23], but they require the privilege that junctions avoid [13]. And a junction is a local-volume mechanism, so a laptop with a second drive is fine, while a roaming profile or a cloud-synced folder may not behave as expected.

The risk profile is therefore asymmetric. Discovery failures are annoying and recoverable. Git duplication is messy but visible. Cleanup data loss is neither. A junction strategy must be designed around the third risk, not the first.

### Finding 5: the bridge should be per-skill, generated, and optional

The evidence supports a simple architecture. Canonical skill content lives in `.agents/skills/<name>/SKILL.md`. That directory is tracked in Git and read natively by Codex, Cursor, OpenCode, and Copilot [3][4][5][6][8]. Claude Code gets a bridge at `.claude/skills/<name>`. The bridge is generated, not authored, and Git ignores it when it consists of links.

Per-skill links are safer than one top-level link for three reasons. First, a failure is isolated: if one host skips one junction, the other skills still load. Second, the layout matches what the `npx skills` installer does and what Claude Code documents about individual skill-folder symlinks [1][14]. Third, it avoids the ambiguity of a junctioned `skills` root, which has been reported as both a workaround and a regression trigger in different Claude Code discussions [14][16]. A top-level link is tempting because it is one command, but it concentrates the failure and complicates bootstrapping on a fresh clone.

The bridge should also be optional. Three situations do not want links at all. CI and cloud agents typically start from a fresh checkout and may not preserve reparse points; a copy is deterministic. Teammates on macOS or Linux may not have permission to create symlinks, and a Windows-created junction does not survive a clone. Agent-managed worktrees may be archived or cleaned by code that traverses reparse points, as the Codex incidents show [17]. In those situations, install by copy with `npx skills add ... --copy`, or with `gh skill install --agent claude-code`, which writes to the host's documented directory and records provenance in the skill frontmatter [5][19][20][22].

The same logic applies at user scope. `~/.agents/skills` is the neutral user store read by Codex, Cursor, OpenCode, and Copilot [3][4][5][8]. Claude Code reads `~/.claude/skills` [1]. A per-skill junction from the latter to the former is the Windows equivalent of the dotfiles symlink pattern, and it is exactly the pattern the `npx skills` installer uses [14][19]. It is also the pattern most likely to hit the Node classification issue, so it should be verified with `/skills` in Claude Code immediately after setup.

One caveat deserves its own sentence: Claude Code's cloud and Cowork sessions do not read the local `~/.claude/skills` directory. They load skills enabled for the claude.ai account, or skills committed to the repository's `.claude/skills/` for cloud sessions other than project threads [1]. A junction-based local setup therefore does not travel to cloud sessions. If cloud use matters, commit real skill directories or publish through a plugin or marketplace, and accept the duplication as a deliberate deployment artifact rather than accidental drift.

### Finding 6: the adapter document needs a compatibility matrix, not a host list

The current document is organized by host, which encourages the reader to think in silos. A compatibility matrix organized by capability makes the actual decision visible: which hosts read the canonical path, which need a bridge, which need a copy, and which have host-specific rule files that must be kept consistent.

The matrix should distinguish four layers. The skill root layer answers where `SKILL.md` lives. The instruction layer answers where always-on rules live. The invocation layer answers whether the host loads skills automatically or requires explicit invocation. The distribution layer answers how a skill reaches a machine: repository checkout, CLI install, plugin, or marketplace. The current document collapses all four into one table and therefore cannot express the fact that Codex and Claude Code can share a skill directory while disagreeing about invocation, or that Copilot can read the same project directory as Cursor while using a different instruction file.

The matrix should also carry dates and versions. The Claude Code `AGENTS.md` behavior changed at v2.1.277 and became more reliable at v2.1.281 [2]. The `gh skill` command is in public preview and requires GitHub CLI 2.90.0 or later [5][22]. Cursor's nested skill discovery and compatibility reads are current as of the October 2026 documentation [4]. A compatibility table without a date is a trap for the next reader, because the underlying products ship weekly.

Finally, the document should state what it does not guarantee. It can say that a path is documented, not that a host will invoke a skill for a given prompt. It can say that a junction is the default installer mechanism on Windows, not that every host's scanner handles it. It can say that `AGENTS.md` is read by Claude Code when no `CLAUDE.md` exists, not that a repository with both files will behave as the author expects. Those distinctions are the difference between a useful adapter guide and a source of confident wrong turns.

## Synthesis and Insights

The first insight is that the compatibility problem inverted. In late 2024 and early 2025, each agent had its own instruction file and its own skill directory; sharing meant duplication. By October 2026, the Agent Skills standard has more than 70 integrating platforms and has been donated to the Agentic AI Foundation under the Linux Foundation [21]. Four of the five hosts in this document read `.agents/skills`, and all five read `AGENTS.md` in some configuration [2][3][4][5][6][8][10]. The remaining asymmetry is concentrated in one product, Claude Code, and in one direction, Claude reading a neutral store. That is a much better problem than the document assumes.

The second insight is that junctions solve a Windows privilege problem, not a compatibility problem. They are the pragmatic way to create directory links without administrator rights, and the ecosystem's most popular installer already relies on them [13][14][19]. But they do not make a host read a directory it does not document, and they introduce two failure modes that symlinks do not: Git treats them as real directories, and some cleanup code treats them as traversable directories. A junction is therefore a bridge implementation, not an architecture. The architecture is the canonical store, and the bridge should be replaceable by a copy without changing the content.

The third insight is that the document's pessimism is self-fulfilling. If the guide says every host needs its own copy, operators create copies, the copies drift, and the next reader concludes that sharing is impossible. If the guide says there is one canonical store and one bridge, operators create one store and one generated bridge, and the drift surface shrinks to the bridge script. Documentation shapes the maintenance behavior it predicts.

The fourth insight is that the risk has moved from discovery to deletion. The interesting failure in 2026 is not "the agent cannot find the skill." It is "the agent found the skill, followed the link, and deleted the target." The Codex incidents are the clearest evidence, and they are severe enough to change the default recommendation: no junctions inside agent-managed worktrees, no junctions in directories that an automated cleanup may own, and a backup before experimenting [17]. Discovery quirks are recoverable; a deleted `node_modules` or assets folder is not always.

## Limitations and Caveats

Vendor documentation is the best available source for path lists, but it is marketing-adjacent and can lag the shipped product. The Claude Code documentation, for example, documents `AGENTS.md` support at v2.1.277 while noting that some sessions before v2.1.281 still could not load it [2]. A reader on an older version may see different behavior than this report describes.

The junction experiments were run on one Windows machine with Node 18.20.7, Python 3.12.0, Git 2.54.0.windows.1, and PowerShell 5.1.26100.9711. The Node classification result matches the Node 24 and Bun 1.3 output reported in the Claude Code issue, but the experiment did not cover every runtime or every host [14]. The deletion experiments covered PowerShell, `cmd`, Node `fs.rmSync`, and `git clean`; they did not cover every cleanup library, and the Codex incident shows that at least one production cleanup path behaves differently [17].

No host was instrumented end-to-end with a junctioned skill in this research. The conclusions about Claude Code discovery rest on vendor documentation and published issue reports, not on a controlled run of the Claude Code binary against a junction. The conclusions about Cursor, OpenCode, and Copilot discovery rest on vendor documentation that does not mention junctions at all. That is the central uncertainty: the mechanism is widely used and often works, but it is not a documented contract for most hosts.

The issue-tracker evidence has the usual biases. Reports are filed by users who hit problems, so the failure rate is unknown. Several reports in this area were withdrawn or reclassified, which is a useful warning against treating a single issue as proof. The Codex data-loss report is stronger because it includes a controlled reproduction, filesystem evidence, and independent corroboration, but it is still a vendor issue thread rather than a peer-reviewed study.

Finally, the report is Windows-centric because the question is about junctions. On macOS and Linux, the equivalent bridge is a symlink, the privilege model is different, and Git stores the link as a link object. The recommendations transfer in shape but not in command syntax.

## Recommendations

**Rewrite `adapters.md` around a canonical store.** Replace the host-by-host skill paths with a verified matrix that names `.agents/skills/` as the shared project root for Codex, Cursor, OpenCode, and Copilot, and `.claude/skills/` as the Claude Code bridge. Keep host-specific paths as secondary rows with a date and a version note. The replacement table should distinguish project scope, user scope, and whether the host reads `.agents/skills` natively.

**Use `AGENTS.md` as the shared instruction file.** Document the Claude Code precedence rule explicitly: a `CLAUDE.md` anywhere in the working directory or above it wins over `AGENTS.md` unless the Project instructions setting is changed. Recommend `@AGENTS.md` import over a symlink for cross-platform repositories, because the symlink shortcut is fragile on Windows and under Git [2].

**Generate the Claude bridge; do not author it.** A bootstrap script should create `.claude/skills/<name>` as a per-skill junction to `../../.agents/skills/<name>` on Windows, or a symlink on macOS and Linux. Add `.claude/skills/` to `.gitignore` when it contains only links. The script should be idempotent and should verify each target after creation.

**Provide a copy mode for non-link environments.** Document `npx skills add <repo> --copy` and `gh skill install <owner>/<repo> <skill> --agent claude-code` as the deterministic alternatives for CI, cloud sessions, teammates, and worktrees [5][19][22]. Make clear that copies are a deployment artifact, not a second source of truth.

**Ban junctions from agent-managed worktrees and cleanup paths.** State the Codex data-loss pattern in one sentence with a citation, and recommend keeping canonical skill content outside worktrees that an agent may archive. If a junction is unavoidable, verify that the cleanup tool unlinks reparse points rather than traversing them, and back up the target first [17].

**Add a verification checklist per host.** After setup, confirm discovery in Claude Code with `/skills`, in Codex with `/skills`, in Cursor under Customize → Skills, and in Copilot through its skills UI or `/skills`. A skill that does not appear should be treated as a bridge failure, not a content failure, and resolved by switching to copy mode.

**Validate the published skill with the standard tooling.** Run `gh skill publish --dry-run` to check the Agent Skills specification before publishing, and keep the `quick_validate.py` check in the repository's test workflow [5][9][22]. The two checks cover different layers: the spec validator covers frontmatter and naming, the health checker covers the discovery log.

## Bibliography

[1] Anthropic. (2026). "Extend Claude with skills." Claude Code Documentation. https://code.claude.com/docs/en/skills (Retrieved: 2026-10-28)

[2] Anthropic. (2026). "How Claude remembers your project." Claude Code Documentation. https://code.claude.com/docs/en/memory (Retrieved: 2026-10-28)

[3] OpenCode. (2026). "Agent Skills." OpenCode Documentation. https://opencode.ai/docs/skills/ (Retrieved: 2026-10-28)

[4] Cursor. (2026). "Agent Skills." Cursor Documentation. https://cursor.com/docs/skills (Retrieved: 2026-10-28)

[5] GitHub. (2026). "Adding agent skills for GitHub Copilot." GitHub Docs. https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills (Retrieved: 2026-10-28)

[6] Microsoft. (2026). "Use Agent Skills in VS Code." Visual Studio Code Documentation. https://code.visualstudio.com/docs/agent-customization/agent-skills (Retrieved: 2026-10-28)

[7] Microsoft. (2026). "Use custom instructions in VS Code." Visual Studio Code Documentation. https://code.visualstudio.com/docs/agent-customization/custom-instructions (Retrieved: 2026-10-28)

[8] OpenAI. (2026). "Build skills." Codex Documentation. https://developers.openai.com/codex/skills (Retrieved: 2026-10-28)

[9] Agent Skills. (2026). "Specification." https://agentskills.io/specification (Retrieved: 2026-10-28)

[10] AGENTS.md. (2026). "AGENTS.md: A simple, open format for guiding coding agents." https://agents.md/ (Retrieved: 2026-10-28)

[11] Microsoft. (2025). "Hard Links and Junctions." Microsoft Learn, Win32 API. https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions (Retrieved: 2026-10-28)

[12] Microsoft. (2026). "mklink." Microsoft Learn, Windows Server Commands. https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/mklink (Retrieved: 2026-10-28)

[13] Git for Windows. (2026). "Git for Windows vs symbolic links." https://gitforwindows.org/symbolic-links.html (Retrieved: 2026-10-28)

[14] sum117. (2026, June 13). "Desktop app omits Windows junction/symlink skills from the / command menu (agent loader resolves them fine)." GitHub issue anthropics/claude-code#68318. https://github.com/anthropics/claude-code/issues/68318 (Retrieved: 2026-10-28)

[15] gotsanity. (2026, March 30). "Skills in ~/.claude/skills/ via directory junctions not resolved at session start (Windows)." GitHub issue anthropics/claude-code#41177. https://github.com/anthropics/claude-code/issues/41177 (Retrieved: 2026-10-28)

[16] tlvenn. (2026, March 24). "User-level skills not loaded when ~/.claude/skills is a symlink (regression since ~v2.1.69)." GitHub issue anthropics/claude-code#38051. https://github.com/anthropics/claude-code/issues/38051 (Retrieved: 2026-10-28)

[17] tyzhr2026-cell et al. (2026, July 22). "[Critical data loss][Windows Desktop] Archiving a managed worktree follows a Junction and deletes files in the external target." GitHub issue openai/codex#34702. https://github.com/openai/codex/issues/34702 (Retrieved: 2026-10-28)

[18] BrodBlox09. (2025, October 26). "Git - repository with directory junction does not mark changed files inside that junction as modified without reloading extensions." GitHub issue microsoft/vscode#273381. https://github.com/microsoft/vscode/issues/273381 (Retrieved: 2026-10-28)

[19] Vercel Labs. (2026). "skills: The CLI for the open agent skills ecosystem." GitHub repository. https://github.com/vercel-labs/skills (Retrieved: 2026-10-28)

[20] sum117. (2026, June 13). "docs: document Windows junctions being invisible to Claude Code's slash menu." Pull request vercel-labs/skills#1435. https://github.com/vercel-labs/skills/pull/1435 (Retrieved: 2026-10-28)

[21] Anthropic. (2026, October 22). "Donating Agent Skills to the Agentic AI Foundation." https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation (Retrieved: 2026-10-28)

[22] GitHub. (2026). "gh skill." GitHub CLI Manual. https://cli.github.com/manual/gh_skill (Retrieved: 2026-10-28)

[23] Microsoft. (2024). "Creating Symbolic Links." Microsoft Learn, Win32 API. https://learn.microsoft.com/en-us/windows/win32/fileio/creating-symbolic-links (Retrieved: 2026-10-28)

## Methodology Appendix

### Research design

The report used the deep-research eight-phase pipeline. Phase 1 defined the two questions and the five-host scope. Phase 2 selected primary sources: vendor skill and instruction documentation for each host, the Agent Skills specification, and the `AGENTS.md` project. Phase 3 retrieved sources in parallel, including official pages and issue trackers. Phase 4 triangulated path claims across at least two sources per host and treated single-source claims as provisional. Phase 4.5 refined the outline after the evidence showed that repository integrity and cleanup risk were more important than discovery quirks. Phase 5 synthesized the inversion, bridge, and self-fulfilling-pessimism insights. Phase 6 critiqued the draft against a skeptical practitioner and an implementation engineer, which led to the explicit separation of discovery, invocation, and distribution. Phase 7 added the local experiments and the cloud-session caveat. Phase 8 packaged the report and the proposed adapter rewrite.

### Source selection and credibility

Official vendor documentation was preferred for path lists and version gates. GitHub issues were used only where they added reproduction evidence or described behavior absent from documentation. The Codex data-loss issue was weighted heavily because it includes a controlled reproduction, before-and-after hashes, environment versions, and two independent corroborating reports. The Claude Code junction issues were weighted cautiously because one was closed as a duplicate of a broader bug, one was withdrawn by its author, and the desktop-menu report was retracted. This asymmetry is reflected in the findings.

### Local experiments

All experiments ran on 2026-10-28 in `C:\TEMP\opencode\junction-test` on Windows, with Node 18.20.7, Python 3.12.0, Git 2.54.0.windows.1, and PowerShell 5.1.26100.9711.

1. **Junction creation and runtime classification.** `cmd /c mklink /J link target` created a junction without elevation. Node `fs.readdirSync(dir, {withFileTypes:true})` reported `link isDirectory=false isSymbolicLink=true`; Python `pathlib.Path` reported `is_dir=True`, `is_symlink=False`, `os.path.realpath` resolved to the target, and `os.listdir` returned the target contents.

2. **Git staging of an in-tree junction.** A repository contained `real/file.txt` and a junction `linked` pointing at `real`. `git add .` staged both `linked/file.txt` and `real/file.txt`; `git ls-files` listed both.

3. **Git staging of an out-of-tree junction.** A repository contained a junction `linked` pointing at an external directory with `external.txt`. `git add .` staged `linked/external.txt` as an ordinary file.

4. **Deletion behavior.** Four paths were tested on separate targets: PowerShell 7 `Remove-Item -Recurse`, `cmd /c rmdir`, Node `fs.rmSync({recursive:true, force:true})`, and `git clean -fdx` on a gitignored junction. Each removed the link and left the target file intact in this environment.

These experiments establish filesystem and Git behavior, not host discovery behavior. They are reported as such.

### Verification and critique

Every factual claim about a host path was checked against that host's documentation. Claims about junction support were checked against documentation first and issue reports second; where documentation was silent, the report says so. The draft was reviewed for the red-team questions: what is missing, what could be wrong, what alternative explanation exists, and what bias might be present. The main correction from that review was to stop treating the Claude Code menu issue as proof of junction failure, because the reporter retracted that attribution. The second correction was to elevate the Codex data-loss evidence above the compatibility evidence, because the consequence is irreversible.

### Reproduction notes

To reproduce the Git finding, create a repository with a real directory and a junction to it, run `git add .`, and inspect `git ls-files`. To reproduce the runtime classification, enumerate the parent directory with Node `withFileTypes` and with Python `pathlib`. To reproduce the deletion finding, create a target with a sentinel file, create a junction, remove the junction with each tool, and check the sentinel after each attempt. Do not run the deletion experiment on a directory you cannot restore.
