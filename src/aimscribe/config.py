import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
PROTOCOL_DIR = DATA / "protocols"
EXTRACT_DIR = DATA / "extracted"
CARDS_PATH = DATA / "cards" / "cards.jsonl"
DRAFTS_PATH = DATA / "cards" / "drafts.jsonl"
INDEX_DIR = DATA / "index"
CASES_PATH = DATA / "cases" / "cases.json"
OUTPUT_DIR = ROOT / "eval" / "outputs"
COLLECTION = "aimscribe_cards"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")  # used only if LLM_PROVIDER=gemini
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

# Replace titles with the exact titles printed on each PDF cover.
PROTOCOLS = {
    "dengue": dict(
        prefix="DEN",
        file="dengue_bd_5th.pdf",
        title="NATIONAL GUIDELINE FOR CLINICAL MANAGEMENT OF DENGUE",
        version="5th edition, 2025",
        pages=[(26, 28), (37, 41), (45, 48)],
    ),
    "hypertension": dict(
        prefix="HTN",
        file="hypertension_bd_2023.pdf",
        title="National Guideline on Hypertension",
        version="Second edition 2023",
        pages=[(46, 52), (64, 65)],
    ),
    "cholera": dict(
        prefix="CHO",
        file="cholera_who_2024.pdf",
        title="Clinical tools for cholera treatment facilities",
        version="v1.0, 2024",
        pages=[(5, 14)],
    ),
    "chikungunya": dict(
        prefix="CHI",
        file="chikungunya_bd_2017.pdf",
        title="NATIONAL GUIDELINE ON CLINICAL MANAGEMENT OF CHIKUNGUNYA FEVER",
        version="First published 15 May 2017",
        pages=[(11, 22), (26, 27)],
    ),
}
CAT_CODE = {
    "probable_diagnosis": "DX",
    "investigation": "IX",
    "medication": "RX",
    "advice": "ADV",
}


def expand(ranges):
    return [p for a, b in ranges for p in range(a, b + 1)]
