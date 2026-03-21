# Dataset Description

## 1. Chatbot Arena Dataset

**Source:**
https://huggingface.co/datasets/lmsys/chatbot_arena_conversations

**Description:**
This dataset contains human preference comparisons between different chatbot responses. It is primarily used for evaluating LLM performance and ranking models based on user feedback.

**Number of instances:** ~33,000+ conversations
**Number of attributes:** Includes prompts, responses, model labels, and preference annotations

**How to download:**
Download using HuggingFace datasets library or from the link above and place it in the `data/chatbot_arena/` folder.

---

## 2. Prompt Library Dataset

**Source:**
https://huggingface.co/datasets/promptslab/awesome-prompts

**Description:**
A curated collection of high-quality prompts used for various AI tasks such as writing, coding, reasoning, and instruction tuning.

**Number of instances:** ~1000+ prompts
**Number of attributes:** Prompt text, category, tags

**How to download:**
Download from HuggingFace and store in `data/prompt_library/`.

---

## 3. ShareGPT Code Interpreter Dataset

**Source:**
https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered

**Description:**
Contains conversations where users interact with AI for coding, debugging, and code execution tasks. Useful for analyzing programming-related prompts and responses.

**Number of instances:** ~70,000+ conversations
**Number of attributes:** User prompts, assistant responses, code snippets

**How to download:**
Download from HuggingFace and place in `data/sharegpt_code_interpreter/`.

---

## 4. ShareGPT Conversation Chronicles Dataset

**Source:**
https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered

**Description:**
A large dataset of real-world conversational data between users and AI assistants, covering multiple domains such as general knowledge, reasoning, and casual chat.

**Number of instances:** ~90,000+ conversations
**Number of attributes:** Conversation threads, roles, message content

**How to download:**
Download from HuggingFace and store in `data/sharegpt_conversation_chronicles/`.

---

## Notes

* These datasets are **not uploaded to the repository** due to their large size.
* All datasets are publicly available and can be downloaded from the provided sources.
* After downloading, organize them inside the `data/` directory as specified.
