def enhance_prompt_stream(text, on_delta=None):
    """Stream the enhanced prompt. Calls on_delta(chunk) as tokens arrive
    and returns the full text when done."""
    if not API_KEY:
        raise RuntimeError("API_KEY is not set. Edit your .env file.")
    url = BASE_URL + "/chat/completions"
    headers = {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": MODEL_ID,
        "temperature": TEMPERATURE,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    pieces = []
    with requests.post(url, headers=headers, json=payload, stream=True,
                       timeout=(10, 120)) as resp:
        if resp.status_code != 200:
            detail = resp.text[:300] if resp.text else ""
            raise RuntimeError("API error %s: %s" % (resp.status_code, detail))
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            if raw.startswith("data: "):
                raw = raw[6:]
            if raw.strip() == "[DONE]":
                break
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            try:
                delta = obj["choices"][0].get("delta", {}).get("content")
            except (KeyError, IndexError, AttributeError):
                delta = None
            if delta:
                pieces.append(delta)
                if on_delta:
                    on_delta(delta)
    result = "".join(pieces).strip()
    if not result:
        raise RuntimeError("Empty response from model.")
    return result
