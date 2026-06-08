import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

MODEL_NAME = "deepseek/deepseek-chat-v3"

FALLBACK_MODELS = [
    "qwen/qwen3-32b",
    "meta-llama/llama-3.3-70b-instruct"
]

MAX_INFERENCE_TOKENS = 1200