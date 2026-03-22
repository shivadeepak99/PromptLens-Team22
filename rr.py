from datasets import load_dataset
import os

BASE_DIR = "raw/datasets"

datasets_to_download = {
    "sharegpt_conversation_chronicles": [
        "RyokoAI/ShareGPT52K",
        "anon8231489123/ShareGPT_Vicuna_unfiltered",
        "DSULT-Core/ShareGPT-X"
    ],
    "sharegpt_code_interpreter": [
        "ajibawa-2023/Code-74k-ShareGPT",
        "sanjay920/Code-Feedback-sharegpt"
    ],
    "chatbot_arena": [
        "lmsys/chatbot_arena_conversations"
    ],
    "prompt_library": [
        # No single dataset — placeholder (you’ll likely build/custom scrape this)
    ]
}

os.makedirs(BASE_DIR, exist_ok=True)

for folder, dataset_list in datasets_to_download.items():
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    for dataset_name in dataset_list:
        try:
            print(f"\n🔥 Downloading {dataset_name}...")
            dataset = load_dataset(dataset_name)

            save_path = os.path.join(folder_path, dataset_name.replace("/", "_"))
            dataset.save_to_disk(save_path)

            print(f"✅ Saved to {save_path}")
        except Exception as e:
            print(f"❌ Failed {dataset_name}: {e}")