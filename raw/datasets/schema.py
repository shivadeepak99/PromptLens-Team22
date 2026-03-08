from datasets import load_from_disk
import os
import pandas as pd

DATASET_ROOT = r"E:\GPls\prompt-lens\promptlens-data\raw\datasets"


def inspect_dataset(dataset_path):

    print("\n======================================")
    print(f"DATASET: {os.path.basename(dataset_path)}")
    print("======================================")

    ds = load_from_disk(dataset_path)

    # Usually datasets are DatasetDict
    if "train" in ds:
        ds = ds["train"]

    print("\n--- Dataset Info ---")
    print(ds)

    print("\n--- Schema ---")
    print(ds.features)

    print("\n--- Number of rows ---")
    print(len(ds))

    print("\n--- First 5 Entries ---")

    sample = ds.select(range(min(5, len(ds))))

    df = pd.DataFrame(sample)
    print(df.to_string())


def main():

    for dataset in os.listdir(DATASET_ROOT):
        if dataset.startswith("_"):
         continue

        dataset_path = os.path.join(DATASET_ROOT, dataset)

        if os.path.isdir(dataset_path):
            inspect_dataset(dataset_path)


if __name__ == "__main__":
    main()