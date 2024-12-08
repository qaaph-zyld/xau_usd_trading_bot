from pathlib import Path

directories = [
    "src/data",
    "src/analysis",
    "src/strategy",
    "src/utils",
    "tests",
    "config",
    "notebooks",
    "data"
]

for dir_path in directories:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {dir_path}")
