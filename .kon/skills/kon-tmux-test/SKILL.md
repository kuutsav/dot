---
name: kon-tmux-test
description: E2E testing of kon using tmux sessions; IMPORTANT: only trigger this skill when user asks for e2e testing of kon
---

# Kon Tmux E2E Testing

End-to-end testing of kon using tmux sessions to programmatically control the TUI application.

## Why Tmux?

Kon is a TUI (Textual-based) app. Running tests programmatically is hard. Tmux provides:
- `tmux new-session` - isolate test environment
- `tmux send-keys` - send keyboard input
- `tmux capture-pane` - capture output
- `tmux has-session` - check if kon is running

## Test Design Philosophy

- **Deterministic**: Shell scripts create reproducible test environments
- **Separation of concerns**: Shell script runs steps and captures output; kon (AI) evaluates results
- **Output-based evaluation**: Test success/failure determined by AI reading output files, not shell script heuristics
- **UI-focused**: Test triggers (@, / commands) by checking UI elements appear
- **Single conversation**: Encourage all tool calls in one query

## Quick Start

```bash
# Run all e2e tests
bash ~/.kon/skills/kon-tmux-test/run-e2e-tests.sh

# After running, kon (the AI) reads the output files and evaluates results
# Output files: /tmp/kon-test-*.txt
```

## Test Scripts

### Setup Script: `setup-test-project.sh`

Creates the same deterministic test project structure each time at `/tmp/kon-test-project/`:

```bash
bash ~/.kon/skills/kon-tmux-test/setup-test-project.sh
```

Test project structure:
```
/tmp/kon-test-project/
├── README.md          # Project documentation
├── config.json       # Config file with basic data
├── notes.txt        # Simple text notes
├── utils.py         # Python utility file
└── data.py          # Python data file
```

### Main Test Script: `run-e2e-tests.sh`

Runs comprehensive e2e tests including UI triggers and tool execution:

```bash
bash ~/.kon/skills/kon-tmux-test/run-e2e-tests.sh
```

## Test Categories

### UI Trigger Tests (LLM-independent)
- **/ commands**: Type `/`, verify slash command list appears with all commands
- **@ file search**: Type `@pyproject`, verify file picker appears with pyproject.toml
- **/model command**: Type `/model`, verify model selector appears, then dismiss
- **/new command**: Type `/new`, verify new conversation is started
- **/resume command**: Type `/resume`, verify session list appears, then dismiss
- **/session command**: Type `/session`, verify session info/statistics displayed

### Tab Path Completion Tests (LLM-independent)
- **Unique match**: Type `sr` + Tab, verify completes to `src/` directly
- **Multiple alternatives**: Type `s` + Tab, verify floating list shows `scripts/`, `src/`
- **Home directory**: Type `~/De` + Tab, verify floating list shows `Desktop/`, `Developer/`, etc.
- **Select from list**: Type `s` + Tab + Enter, verify `scripts/` is applied to input

### Tool Execution Tests (File system verification)
- **Write tool**: Creates files, verified by file existence
- **Edit tool**: Modifies files, verified by file content
- **List files**: Shows directory contents, verified by output
- **Calculation**: Computes results, verified by LLM output (acceptable for non-tool operations)

## Running Tests

```bash
# Run all tests - script executes steps and captures output
bash ~/.kon/skills/kon-tmux-test/run-e2e-tests.sh

# After running, the AI (kon) reads output files and provides evaluation:
# - /tmp/kon-test-1-commands.txt       (/ slash commands list)
# - /tmp/kon-test-2-at-trigger.txt     (@ file picker test)
# - /tmp/kon-test-3-model.txt          (/model selector test)
# - /tmp/kon-test-4-new.txt            (/new conversation test)
# - /tmp/kon-test-5-tab-unique.txt     (Tab completion unique match)
# - /tmp/kon-test-6-tab-multiple.txt   (Tab completion floating list)
# - /tmp/kon-test-7-tab-home.txt       (Tab completion home directory)
# - /tmp/kon-test-8-tab-select.txt     (Tab completion select from list)
# - /tmp/kon-test-9-tools.txt          (tool execution test)
# - /tmp/kon-test-10-session.txt       (/session stats test)
# - /tmp/kon-test-11-resume.txt        (/resume session list test)
# - /tmp/kon-test-files.txt            (file system state)
# - /tmp/kon-test-test1-content.txt    (test1.txt content)
```

## Configuration

Edit `run-e2e-tests.sh` to adjust:

```bash
WAIT_TIME=30          # Time for LLM to complete all tasks (adjust based on model speed)
COMMAND_WAIT_TIME=3   # Time for UI commands to settle
SESSION_NAME="kon-test"  # Tmux session name
TEST_DIR="/tmp/kon-test-project"  # Test project directory for tool execution
KON_DIR="$HOME/Developer/personal/kon"  # Kon repo directory (for tab completion tests)
```

## Key Tmux Gotchas

- **Use `Escape` not `Esc`**: tmux recognizes `Escape` as the escape key. `Esc` is NOT a valid key name and sends literal characters 'E', 's', 'c' as text.
- **Always clear input between tests**: Use `Escape` to dismiss completions, then `C-u` to clear text. Without this, text from one test bleeds into the next.
- **Completion selectors block input**: The model selector and session list intercept Enter/Escape. Always dismiss them with `Escape` before the next test.

## Test Evaluation (by Kon)

After running the test script, kon evaluates the results by reading the output files:

### What to Check

**UI Trigger Tests (by reading output files):**
- `/` test: Slash command list appears showing commands (help, model, new, etc.)
- `@` test: File picker appears and shows files (pyproject.toml)
- `/model` test: Model selector appears with model list
- `/new` test: "Started new conversation" message appears
- `/resume` test: Session list appears with prior sessions
- `/session` test: Session info/statistics displayed (messages, tokens)

**Tab Path Completion Tests (by reading output files):**
- `sr` + Tab test: Input shows `src/` (unique completion applied)
- `s` + Tab test: Floating list visible with `scripts/` and `src/` options
- `~/De` + Tab test: Floating list visible with `Desktop/`, `Developer/`, `Documents/`, `Downloads/`
- `s` + Tab + Enter test: Input shows `scripts/` (selection applied)

**Tool Execution Tests (by reading output files + file system):**
- `test1.txt` created in /tmp/kon-test-project/
- `test1.txt` contains "world" (not "hello")
- Directory listing shows files

### Tabular Report

Kon provides a tabular summary after reading all output files, showing:
- Test name
- Status (PASS/FAIL)
- Description
- Overall success rate

### IMPORTANT: Always offer the view command

After presenting the tabular report, ALWAYS give the user this shell command so they can inspect the raw captured outputs in their terminal:

```bash
for f in /tmp/kon-test-*.txt; do printf "\n\033[1;36m▶▶▶ %s\033[0m\n" "$f"; awk 'NF{found=1} found{lines[++n]=$0} END{while(n>0 && lines[n]=="") n--; for(i=1;i<=n;i++) print lines[i]}' "$f"; done
```

## Cleanup

```bash
# Test script auto-cleans tmux session on exit via trap
# Output files remain for kon to evaluate (/tmp/kon-test-*.txt)
# Manual cleanup if needed:
tmux kill-session -t kon-test 2>/dev/null
rm -rf /tmp/kon-test-project
rm -f /tmp/kon-test-*.txt
```

## Tmux Commands Reference

```bash
# Session management
tmux new-session -d -s <name> -c <dir> '<command>'  # Create detached session
tmux kill-session -t <name>                        # Kill session
tmux has-session -t <name>                         # Check if session exists

# Input — IMPORTANT: use full key names (Escape, Enter, not Esc)
tmux send-keys -t <name> "text"    # Send text
tmux send-keys -t <name> Enter     # Send Enter key
tmux send-keys -t <name> Escape    # Send Escape key (NOT "Esc"!)
tmux send-keys -t <name> Tab       # Send Tab key
tmux send-keys -t <name> C-c       # Send Ctrl+C
tmux send-keys -t <name> C-u       # Send Ctrl+U (clear line)

# Output
tmux capture-pane -t <name> -p     # Capture pane to stdout
tmux capture-pane -t <name> -p > file.txt  # Save to file
```

## Tips

- Tests are deterministic: same project structure recreated each run
- UI tests don't depend on LLM: verify TUI elements appear
- Tab completion tests run from kon repo to test on known directory structure
- Tool tests verify file system: check actual files, not LLM output
- Use `trap cleanup EXIT` to ensure tmux session is always cleaned up
- Adjust `WAIT_TIME` based on model speed for tool execution tests
- Output files saved to `/tmp/kon-test-*.txt` for debugging
- Run tool execution before /resume so there's a session with messages in the list
