"""
Script to replace all print statements with logger calls
"""

import re
import os

files_to_process = [
    "Libs/RAG.py",
    "Logic/API/api_wrapper.py",
    "Utils/ai_agent.py",
    "Logic/API/ai/builder.py",
]

# Replacements map for emojis and special characters
replacements = [
    # Emojis to ASCII
    (r"✅", "[OK]"),
    (r"❌", "[ERROR]"),
    (r"⚠️", "[WARNING]"),
    (r"📊", ">>"),
    (r"🏷️", "[TAG]"),
    (r"💻", "[CODE]"),
    (r"🎯", "[TARGET]"),
    (r"📋", "[CLIPBOARD]"),
    (r"🚀", "[EXEC]"),
    (r"🔍", "[SEARCH]"),
    (r"🔄", "[RETRY]"),
    (r"📚", "[DOCS]"),
    (r"🤖", "[AI]"),
    (r"📡", "[API]"),
    # Box drawing characters
    (r"└──", "+--"),
    (r"├──", "+--"),
    (r"│", "|"),
    (r"─", "-"),
    (r"┌", "+"),
    (r"┐", "+"),
    (r"┘", "+"),
    (r"└", "+"),
    (r"├", "+"),
    (r"┤", "+"),
]

for filepath in files_to_process:
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - file not found")
        continue

    print(f"Processing {filepath}...")

    # Read the file
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Apply replacements
    for old, new in replacements:
        content = content.replace(old, new)

    # Replace print( with log.safe_print(
    content = re.sub(
        r"^(\s*)print\(", r"\1log.safe_print(", content, flags=re.MULTILINE
    )

    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Done processing {filepath}")

print("\nAll files processed!")
