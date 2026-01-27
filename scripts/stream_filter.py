#!/usr/bin/env python3
"""Filter Claude CLI stream-json output to human-readable text.

Reads JSON lines from stdin, extracts text content, and prints formatted output.
Passes through non-JSON lines as-is.
"""

import json
import sys


def process_line(line: str) -> str | None:
    """Extract human-readable text from a stream-json line."""
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        # Not JSON, pass through as-is
        return line

    # Handle different message types from Claude CLI stream-json
    msg_type = data.get("type", "")

    # Assistant text content
    if msg_type == "assistant":
        content = data.get("message", {}).get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        if texts:
            return "".join(texts)

    # Content block delta (streaming text)
    if msg_type == "content_block_delta":
        delta = data.get("delta", {})
        if delta.get("type") == "text_delta":
            return delta.get("text", "")

    # Content block start
    if msg_type == "content_block_start":
        block = data.get("content_block", {})
        if block.get("type") == "text":
            return block.get("text", "")

    # Tool use
    if msg_type == "tool_use":
        tool_name = data.get("name", "unknown")
        return f"\n[Tool: {tool_name}]\n"

    # Result message (final output)
    if msg_type == "result":
        result_text = data.get("result", "")
        if result_text:
            return f"\n--- Result ---\n{result_text}\n"

    # System messages
    if msg_type == "system":
        return f"[System: {data.get('message', '')}]"

    # Error messages
    if msg_type == "error":
        return f"[Error: {data.get('message', data.get('error', ''))}]"

    return None


def main():
    """Process stdin and output formatted text."""
    # Use unbuffered output for real-time display
    for line in sys.stdin:
        output = process_line(line)
        if output:
            print(output, end="", flush=True)
    # Ensure final newline
    print()


if __name__ == "__main__":
    main()
