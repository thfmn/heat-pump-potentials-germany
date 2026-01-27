#!/usr/bin/env bash
# ralph-custom.sh
# Usage: ./ralph-custom.sh [-h|--human-readable] <iterations>

set -euo pipefail

# Parse flags
human_readable=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--human-readable)
      human_readable=true
      shift
      ;;
    -*)
      echo "Unknown option: $1"
      echo "Usage: $0 [-h|--human-readable] <iterations>"
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [-h|--human-readable] <iterations>"
  echo "  -h, --human-readable  Display output in human-readable format"
  exit 1
fi

iterations="$1"
if ! [[ "$iterations" =~ ^[0-9]+$ ]] || [[ "$iterations" -lt 1 ]]; then
  echo "Error: iterations must be a positive integer"
  exit 1
fi

prompt=$'@PRD.md @progress.txt\n\
\n\
=== MICRO-TASK MODE: ONE CHECKBOX ONLY ===\n\
\n\
🔴 CRITICAL: GOOGLE CLOUD COST CONSTRAINTS 🔴\n\
We have a $10 budget total. We MUST NOT exceed this. BEFORE running ANY Google Cloud command:\n\
1. Check if the command will incur charges (gcloud billing list, documentation)\n\
2. Prefer free tier services and operations (Cloud Storage operations are FREE)\n\
3. AVOID: BigQuery (metered), Cloud Run with high concurrency, Dataflow, high-traffic Cloud Logging\n\
4. Do NOT run anything exploratory or experimental on real GCP resources\n\
5. Keep all deployments minimal and use free/included quotas only\n\
6. When in doubt, ASK or use dry-run flags (--dry-run, --no-op, --validate-only)\n\
⚠️  One mistake here means losing our $10 budget and failing the project.\n\
\n\
1. Pick ONE unchecked checkbox ([ ]) from ISSUES.md - highest priority, not blocked. Always use progress.txt to tell what you are going to work on before you start working on it.\n\
2. Get current timestamp by running: python3 scripts/get_timestamp.py (returns yyyy-MM-dd HH:mm:ss in Asia/Bangkok timezone)\n\
3. Log in progress.txt: timestamp + "START: [task name]"\n\
4. Implement ONLY that single checkbox. Nothing else.\n\
5a. Check off [x] that ONE (MAIN task-)checkbox in ISSUES.md.\n\

This means you are allowed to work on all tasks associated with "Clean `notebooks/district_map_generation.ipynb`" in the following example in a single session, if the complexity is not medium-high. Should one sub-task contain a high-complexity task, break it up before working on it. 

**Tasks**:
- [x] Clean `notebooks/district_map_generation.ipynb`:
  - [x] Clear all output cells (Cell → All Output → Clear)
  - [x] Add markdown cell at top: Title, Purpose, Author, Date
  - [x] Add Table of Contents markdown cell
  - [x] Section 1: "Data Fetching" - explain FfE API
  - [x] Section 2: "Data Transformation" - explain preprocessing
  - [x] Section 3: "Geometry Processing" - explain WKT handling
  - [x] Section 4: "Export" - explain CSV generation
  - [x] Add inline comments explaining complex operations
  - [x] Verify notebook runs end-to-end without errors


5b. Check off ALL acceptance criterea when reached. Do not move on when acceptance criterea for a feature are not satisfied.
6. Get timestamp again and log in progress.txt: timestamp + "DONE: [task name]"\n\
7. Commit your changes often.\n\
8. Use context7 MCP for library docs before you start coding with any library or framework.\n\
9. When updating .txt or .md files, use the Write tool, not Bash redirection.\n\
\n\
⛔ STOP IMMEDIATELY after completing ONE checkbox.\n\
⛔ Do NOT continue to other tasks.\n\
⛔ Do NOT implement "related" or "dependent" tasks.\n\
**Push back on bad architectural and methodical decisions. Be solid, and always well founded and grounded. Striving for verifiably working, clear and not overly complicated solutions.
**We work in a hospital and this is a high-stakes situation. When you do mistakes, we not only are at risk of losing our jobs, but also risk lives.**\n\
If any command requires approval, output the string we have to add to our --allowedTools List like "Bash(ls:*)", including a timestamp.\n\
\n\
Only output <promise>COMPLETE</promise> if EVERY SINGLE checkbox\n\
in the ENTIRE ISSUES.md file is already checked [x].\n'

for ((i=1; i<=iterations; i++)); do
  echo ""
  echo " ╔════════════════════════════════════════════════════════════════╗"
  echo "                      ITERATION $i of $iterations                  "
  echo " ╚════════════════════════════════════════════════════════════════╝"
  echo ""

  # Build claude command based on human-readable flag
  claude_args=(
    --permission-mode acceptEdits
    --allowedTools
      "Bash(ls:*)"
      "Bash(cat:*)"
      "Bash(head:*)"
      "Bash(tail:*)"
      "Bash(grep:*)"
      "Bash(find:*)"
      "Bash(awk:*)"
      "Bash(sed:*)"
      "Bash(uv run:*)"
      "Bash(uv lock:*)"
      "Bash(uv sync:*)"
      "Bash(uv add:*)"
      "Bash(uv pip:*)"
      "Bash(python:*)"
      "Bash(python3:*)"
      "Bash(git:*)"
      "Bash(gcloud services enable:*)"
      "Bash(gcloud projects:*)"
      "Bash(gcloud config:*)"
      "Bash(gcloud iam:*)"
      "Bash(gcloud artifacts:*)"
      "Bash(gcloud auth:*)"
      "Bash(gcloud run:*)"
      "Bash(dbt:*)"
      "Bash(docker:*)"
      "Bash(docker-compose:*)"
      "Bash(curl:*)"
      "Bash(date:*)"
      "Bash(TZ=*)"
      "Edit" "Write"
    --verbose
    -p "$prompt"
  )

  # Always use stream-json for real-time output, optionally filter for readability
  claude_args=(--output-format stream-json "${claude_args[@]}")

  if [[ "$human_readable" == "false" ]]; then
    # JSON mode: show raw JSON (original behavior)
    result="$(claude "${claude_args[@]}" 2>&1 | tee /dev/tty)"
  else
    # Human-readable mode: filter JSON to formatted text
    # Use tee to capture raw output while displaying filtered version
    result="$(claude "${claude_args[@]}" 2>&1 | tee >(python3 scripts/stream_filter.py >/dev/tty))"
  fi

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete, exiting."
    exit 0
  fi

  if [[ "$result" == *"This command requires approval"* ]]; then
    echo "Error: A command wasn't matched by --allowedTools. Expand the allowlist."
    exit 2
  fi
done
