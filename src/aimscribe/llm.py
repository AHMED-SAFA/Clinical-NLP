import json, re
import requests
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_not_exception_type,
)
from . import config as C


class FatalLLMError(Exception):
    """Auth/bad-request errors: retrying will not help."""


def model_info() -> str:
    return (
        f"groq:{C.GROQ_MODEL}"
        if C.LLM_PROVIDER == "groq"
        else f"ollama:{C.OLLAMA_MODEL}"
    )


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _groq(system, user, schema):
    if schema:  # json_object mode does not enforce a schema, so put it in the prompt
        system += (
            "\n\nReturn ONLY a JSON object matching this JSON Schema:\n"
            + json.dumps(schema.model_json_schema())
        )
    body = dict(
        model=C.GROQ_MODEL,
        temperature=C.TEMPERATURE,
        seed=0,
        max_tokens=10000,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    if C.GROQ_MODEL.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"
    for attempt in range(2):
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {C.GROQ_API_KEY}"}, json=body, timeout=120)
        if r.status_code == 400 and "json_validate_failed" in r.text and attempt == 0:
            body.pop("seed", None)
            body["temperature"] = 0.3
            continue
        break
    if r.status_code in (400, 401, 403, 404, 413):
        raise FatalLLMError(f"Groq {r.status_code}: {r.text[:300]}")
    r.raise_for_status()
    return _parse(r.json()["choices"][0]["message"]["content"])


def _ollama(system, user, schema):
    body = dict(
        model=C.OLLAMA_MODEL,
        stream=False,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        format=schema.model_json_schema() if schema else "json",
        options=dict(temperature=C.TEMPERATURE, seed=0),
    )
    r = requests.post(f"{C.OLLAMA_HOST}/api/chat", json=body, timeout=600)
    r.raise_for_status()
    return _parse(r.json()["message"]["content"])


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=15, max=90),
    retry=retry_if_not_exception_type(FatalLLMError),
    reraise=True,
)
def generate_json(
    system: str, user: str, schema: type[BaseModel] | None = None
) -> dict:
    if C.LLM_PROVIDER == "groq":
        return _groq(system, user, schema)
    if C.LLM_PROVIDER == "ollama":
        return _ollama(system, user, schema)
    raise ValueError(f"Unknown LLM_PROVIDER {C.LLM_PROVIDER}")
