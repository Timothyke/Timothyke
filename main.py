"""
ChatGPT Automation Script

This script allows you to automate tasks using the OpenAI ChatGPT API.
It interprets your natural language requests (e.g., 'summarize files in this folder', 'generate reports from data.txt'),
reads or writes local files as needed, and returns/save results.

Requirements:
- Python 3.8+
- `openai` package (`pip install openai`)

Usage:
    python main.py

Configuration:
- Set your OpenAI API key and preferences in the CONFIG section below.

Extensibility:
- Add new commands to the `COMMANDS` dictionary and implement their handlers.

Author: Your Name
Date: 2025-10-23
"""

import os
import sys
import openai
import asyncio
from typing import Optional, Dict, Any, Callable
from pathlib import Path

# ================= CONFIGURATION =================

CONFIG = {
    "OPENAI_API_KEY": "your-openai-api-key-here",  # <-- Put your key here!
    "MODEL": "gpt-4-turbo",
    "TEMPERATURE": 0.7,
    "MAX_TOKENS": 1500,
}

# ================= UTILITY FUNCTIONS =================

def log(msg: str):
    """Print a clean, user-friendly log message."""
    print(f"[LOG] {msg}")

def error(msg: str):
    """Print an error message."""
    print(f"[ERROR] {msg}", file=sys.stderr)

def prompt_user() -> str:
    """Prompt the user for input."""
    print("\nEnter your automation request (e.g., 'summarize files in this folder'):\")
    return input("> ").strip()

def get_text_from_file(file_path: Path) -> Optional[str]:
    """Read text from a file; return None if error."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        error(f"Could not read file {file_path}: {e}")
        return None

def save_output_to_file(output: str, filename: str) -> None:
    """Save output string to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
        log(f"Output saved to {filename}")
    except Exception as e:
        error(f"Failed to save output to {filename}: {e}")

# ================= OPENAI API CALL =================

async def chatgpt_prompt(system_msg: str, user_msg: str) -> str:
    """
    Send messages to OpenAI Chat API, return the response string.
    Handles errors and retries.
    """
    openai.api_key = CONFIG["OPENAI_API_KEY"]

    try:
        response = await openai.ChatCompletion.acreate(
            model=CONFIG["MODEL"],
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=CONFIG["TEMPERATURE"],
            max_tokens=CONFIG["MAX_TOKENS"],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        error(f"OpenAI API error: {e}")
        return ""

# ================= COMMANDS HANDLERS =================

async def summarize_folder(args: Dict[str, Any]) -> str:
    """
    Summarize all text files in a target folder.
    - args['folder'] = folder path (str)
    """
    folder = args.get("folder", ".")
    folder_path = Path(folder).resolve()
    if not folder_path.is_dir():
        return f"Folder '{folder}' does not exist."

    log(f"Scanning folder: {folder_path}")

    text_files = list(folder_path.glob("*.txt"))
    if not text_files:
        return "No text files found in the folder."

    summaries = []
    for file in text_files:
        log(f"Reading file: {file.name}")
        content = get_text_from_file(file)
        if content:
            summary = await chatgpt_prompt(
                system_msg="You are a helpful assistant that summarizes text files.",
                user_msg=f"Summarize the following file named '{file.name}':\n\n{content}"
            )
            summaries.append(f"--- {file.name} ---\n{summary}\n")
        else:
            summaries.append(f"--- {file.name} ---\n[Could not read file]\n")

    result = "\n".join(summaries)
    save_output_to_file(result, "summaries.txt")
    return result

async def generate_json_report(args: Dict[str, Any]) -> str:
    """
    Generate a JSON report from a notes file.
    - args['file'] = file path (str)
    """
    file = args.get("file")
    if not file:
        return "Please specify the notes file."

    file_path = Path(file).resolve()
    content = get_text_from_file(file_path)
    if not content:
        return f"Could not read file '{file}'."

    log(f"Generating JSON report from: {file_path.name}")

    report = await chatgpt_prompt(
        system_msg="You are an assistant that turns notes into structured JSON reports.",
        user_msg=f"Generate a JSON report based on these notes:\n\n{content}"
    )

    # Optional: Try to pretty-print JSON if possible
    try:
        import json
        report_json = json.loads(report)
        pretty_report = json.dumps(report_json, indent=2)
    except Exception:
        pretty_report = report  # Fallback if not valid JSON

    save_output_to_file(pretty_report, "report.json")
    return pretty_report

async def rewrite_and_format(args: Dict[str, Any]) -> str:
    """
    Rewrite and format the given text file.
    - args['file'] = file path (str)
    """
    file = args.get("file")
    if not file:
        return "Please specify the text file to rewrite/format."

    file_path = Path(file).resolve()
    content = get_text_from_file(file_path)
    if not content:
        return f"Could not read file '{file}'."

    log(f"Rewriting and formatting: {file_path.name}")

    rewritten = await chatgpt_prompt(
        system_msg="You are an editor that rewrites and formats text for clarity and readability.",
        user_msg=f"Rewrite and format the following text:\n\n{content}"
    )
    save_output_to_file(rewritten, f"{file_path.stem}_formatted.txt")
    return rewritten

# ================= COMMANDS REGISTRY =================

COMMANDS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "summarize_folder": summarize_folder,
    "generate_json_report": generate_json_report,
    "rewrite_and_format": rewrite_and_format,
}

def parse_command(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse user input into a command and its arguments.
    Returns: dict with 'cmd' and args, or None."""
    # Simple keyword matching for demo purposes.
    # For production, use intent classification or NLP.
    input_lower = user_input.lower()

    if "summarize" in input_lower and "folder" in input_lower:
        # e.g., "summarize files in this folder" or "summarize folder ./notes"
        import re
        match = re.search(r'folder\s+([^\s]+)', input_lower)
        folder = match.group(1) if match else "."
        return {"cmd": "summarize_folder", "folder": folder}
    elif "report" in input_lower and ("json" in input_lower or "generate" in input_lower):
        # e.g., "generate json report from data.txt"
        import re
        match = re.search(r'from\s+([^\s]+)', input_lower)
        file = match.group(1) if match else None
        return {"cmd": "generate_json_report", "file": file}
    elif ("rewrite" in input_lower or "format" in input_lower) and "file" in input_lower:
        # e.g., "rewrite and format file notes.txt"
        import re
        match = re.search(r'file\s+([^\s]+)', input_lower)
        file = match.group(1) if match else None
        return {"cmd": "rewrite_and_format", "file": file}
    else:
        return None

# ================= MAIN EXECUTION =================

async def main():
    log("ChatGPT Automation Script")
    log("Ready for your command.")

    # Check API key
    if not CONFIG["OPENAI_API_KEY"] or CONFIG["OPENAI_API_KEY"].startswith("your-"):
        error("Please set your OpenAI API key in the CONFIG section.")
        return

    while True:
        user_input = prompt_user()
        if user_input.lower() in {"exit", "quit"}:
            log("Exiting. Goodbye!")
            break

        parsed = parse_command(user_input)
        if not parsed:
            error("Could not understand your request. Try something like 'summarize files in this folder'.")
            continue

        cmd = parsed.pop("cmd")
        handler = COMMANDS.get(cmd)
        if not handler:
            error(f"Command '{cmd}' not recognized.")
            continue

        log(f"Executing: {cmd}")
        try:
            result = await handler(parsed)
            print("\n=== RESULT ===\n")
            print(result)
            print("\n==============\n")
        except Exception as e:
            error(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    # For async main
    asyncio.run(main())