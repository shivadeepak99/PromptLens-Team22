import os
from pathlib import Path

DATASET_ROOT = r"E:\GPls\prompt-lens\promptlens-data\raw\datasets"


def get_size(size):
    for unit in ['B','KB','MB','GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def scan_directory(path, depth=0):
    indent = "  " * depth
    items = sorted(os.listdir(path))

    for item in items:
        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            print(f"{indent}[DIR] {item}")
            scan_directory(full_path, depth + 1)

        else:
            size = os.path.getsize(full_path)
            ext = Path(item).suffix
            print(f"{indent}{item} ({ext}) - {get_size(size)}")


def dataset_summary(root):
    print("\n=== DATASET ROOT ===\n")
    print(root)

    for dataset in os.listdir(root):
        dataset_path = os.path.join(root, dataset)

        if os.path.isdir(dataset_path):
            print("\n====================================")
            print(f"DATASET: {dataset}")
            print("====================================")
            scan_directory(dataset_path)


if __name__ == "__main__":
    dataset_summary(DATASET_ROOT)