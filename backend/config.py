import os
from dotenv import load_dotenv

# Load from both the backend directory and the project root directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))
load_dotenv(os.path.join(root_dir, ".env"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


MODEL_NAME = os.getenv("MODEL_NAME", "deepseek/deepseek-chat-v3")

FALLBACK_MODELS = [
    model.strip() for model in os.getenv("FALLBACK_MODELS", "qwen/qwen3-32b,meta-llama/llama-3.3-70b-instruct").split(",")
]

MAX_INFERENCE_TOKENS = int(os.getenv("MAX_INFERENCE_TOKENS", "1200"))