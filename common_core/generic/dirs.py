from pathlib import Path


def create_nested_directory(path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"Directory '{path}' created successfully.")
    except OSError as error:
        print(f"Error creating directory '{path}': {error}")
