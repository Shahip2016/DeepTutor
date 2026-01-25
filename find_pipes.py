import os
from pathlib import Path

def find_pipe_operators(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = Path(root) / file
                try:
                    content = path.read_text(encoding='utf-8')
                    if '| None' in content or '| str' in content or '| int' in content:
                         # Check if it's likely a type hint
                         print(f"FOUND in {path}")
                except Exception:
                    pass

if __name__ == "__main__":
    find_pipe_operators("src")
