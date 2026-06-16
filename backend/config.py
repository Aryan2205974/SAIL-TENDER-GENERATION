import os
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir    = os.path.dirname(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))
load_dotenv(os.path.join(root_dir,    ".env"))

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
NVIDIA_API_KEY     = os.getenv("NVIDIA_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # kept as last resort
OLLAMA_BASE_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# ── Provider → (base_url, api_key) map ───────────────────────────────────────
# Each entry: (base_url, api_key, [model_ids_in_priority_order])
# Gemini uses OpenAI-compatible endpoint via generativelanguage.googleapis.com
PROVIDER_CHAINS = []

if GEMINI_API_KEY:
    PROVIDER_CHAINS.append({
        "name":     "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key":  GEMINI_API_KEY,
        # gemini-2.5-flash: 1M TPM, 1500 RPD — best free API available
        # gemini-2.5-flash-lite: 1M TPM, 1500 RPD — faster, lighter fallback
        "models":   ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
        "tpm_limit": 1_000_000,
    })

if GROQ_API_KEY:
    PROVIDER_CHAINS.append({
        "name":     "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key":  GROQ_API_KEY,
        "models":   ["llama-3.3-70b-versatile", "qwen/qwen3-32b", "llama-3.1-8b-instant"],
        "tpm_limit": 12_000,
    })

if NVIDIA_API_KEY:
    PROVIDER_CHAINS.append({
        "name":     "NVIDIA",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key":  NVIDIA_API_KEY,
        # NVIDIA NIM free: no TPM limit but 40 RPD cap — use as last resort
        "models":   ["meta/llama-3.3-70b-instruct", "qwen/qwen2.5-72b-instruct"],
        "tpm_limit": 999_999,
    })

if OPENROUTER_API_KEY and not OPENROUTER_API_KEY.startswith("your_"):
    PROVIDER_CHAINS.append({
        "name":     "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key":  OPENROUTER_API_KEY,
        "models":   ["google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct"],
        "tpm_limit": 999_999,
    })

if not PROVIDER_CHAINS:
    print("\n[config] ERROR: No API keys found. Set at least one of:\n"
          "  GEMINI_API_KEY  → https://aistudio.google.com/apikey (recommended)\n"
          "  GROQ_API_KEY    → https://console.groq.com\n"
          "  NVIDIA_API_KEY  → https://build.nvidia.com\n")

# Legacy flat list — still used by parts of the code that haven't been updated
MODEL_NAME      = PROVIDER_CHAINS[0]["models"][0] if PROVIDER_CHAINS else "gemini-2.5-flash"
FALLBACK_MODELS = []
for p in PROVIDER_CHAINS[1:]:
    FALLBACK_MODELS.extend(p["models"])

MAX_INFERENCE_TOKENS = int(os.getenv("MAX_INFERENCE_TOKENS", "1500"))
TIMEOUT_SEC          = float(os.getenv("TIMEOUT_SEC", "60"))

print(f"[config] Active providers: {[p['name'] for p in PROVIDER_CHAINS]}")