#!/usr/bin/env python3
"""
Generate explanations for every prompt in data/prompts.csv, using the settings from the original study
(temperature 0.3, max 2,000 tokens, no system prompt).

Setup (once):
    pip install openai
    export OPENAI_API_KEY="sk-..."          # GPT-4o, from platform.openai.com
    export OPENROUTER_API_KEY="sk-or-..."   # both Llama models, from openrouter.ai

Groq retired llama-3.3-70b-versatile and llama-3.1-8b-instant on 16 Aug 2026,
so the Llama models are rerun through OpenRouter (same open weights), asking for
Groq as provider first and DeepInfra second. The provider that answered is recorded.

Run (from the folder containing generations.csv):
    python3 scripts/generate.py data/prompts.csv

Output: generations_rerun.csv
The script is resumable. If it stops (rate limit, daily cap, lost connection),
run the same command again and it continues where it left off.
"""
import csv, os, sys, time, datetime

try:
    from openai import OpenAI, RateLimitError, NotFoundError, APIError
except ImportError:
    sys.exit("Install the client first:  pip install openai")

REPS = 3                 # extra generations per prompt
TEMPERATURE = 0.3        # same as the original run
MAX_TOKENS = 2000        # same as the original run
GROQ_PAUSE = 1.0         # seconds between Llama calls, to be gentle on rate limits
OUT = "generations_rerun.csv"
FIELDS = ["uid", "rep", "topic_id", "grade", "subject", "lang", "model_code", "model_label",
          "requested_model", "returned_model", "provider", "system_fingerprint", "finish_reason",
          "tokens_in", "tokens_out", "timestamp", "response"]

def need(var):
    v = os.environ.get(var)
    if not v:
        sys.exit(f"Missing {var}. Set it with:  export {var}=\"your-key\"")
    return v

openai_client = OpenAI(api_key=need("OPENAI_API_KEY"))
or_client = OpenAI(api_key=need("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
client_for = {"A": openai_client, "B": or_client, "C": or_client}
# original Groq model ids -> the same models on OpenRouter
OR_MODEL = {"llama-3.3-70b-versatile": "meta-llama/llama-3.3-70b-instruct",
            "llama-3.1-8b-instant": "meta-llama/llama-3.1-8b-instruct"}
OR_PROVIDERS = {"order": ["Groq", "DeepInfra"], "allow_fallbacks": False}

def call(client, model, prompt, is_groq):
    extra = {"provider": OR_PROVIDERS} if is_groq else None
    """One generation with retries. Returns the API response, or exits cleanly on hard limits."""
    for attempt in range(8):
        try:
            if is_groq:
                time.sleep(GROQ_PAUSE)
            kw = dict(model=model,
                      messages=[{"role": "user", "content": prompt}],   # no system prompt, as in the original
                      temperature=TEMPERATURE,
                      max_tokens=MAX_TOKENS)
            if extra:
                kw["extra_body"] = extra
            return client.chat.completions.create(**kw)
        except NotFoundError:
            sys.exit(f"\nModel '{model}' is no longer available on this API. "
                     f"Change the model name in OR_MODEL and run again.")
        except RateLimitError as e:
            wait = 20 * (attempt + 1)
            try:
                ra = e.response.headers.get("retry-after")
                if ra:
                    wait = float(ra)
            except Exception:
                pass
            if wait > 300:
                sys.exit(f"\nRate limit says wait {wait/60:.0f}+ minutes (probably a daily cap). "
                         f"Progress is saved. Run the same command again later and it will resume.")
            print(f"   rate limited, waiting {wait:.0f}s ...")
            time.sleep(wait)
        except APIError as e:
            print(f"   API error ({e.__class__.__name__}), retrying in 15s ...")
            time.sleep(15)
    sys.exit("\nToo many failed attempts in a row. Progress is saved; run again later.")

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 scripts/generate.py data/prompts.csv")
    with open(sys.argv[1], encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} original prompts. Planning {len(rows) * REPS} new generations.")

    # upgrade a file written by the first version of this script (no provider column)
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = list(csv.DictReader(f))
        if old and "provider" not in old[0]:
            with open(OUT, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
                for r in old:
                    r["provider"] = "OpenAI" if r["model_code"] == "A" else ""
                    w.writerow({k: r.get(k, "") for k in FIELDS})
    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            done = {(r["uid"], r["rep"]) for r in csv.DictReader(f)}
        print(f"Resuming: {len(done)} already done.")

    new_file = not os.path.exists(OUT)
    with open(OUT, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        # reps on the outside, so if it stops early you still have complete repeats
        for rep in range(2, REPS + 2):          # original run = rep 1; new runs = rep 2, 3, 4
            for i, r in enumerate(rows, 1):
                if (r["uid"], str(rep)) in done:
                    continue
                code = r["model_code"]
                model = OR_MODEL.get(r["model_name"], r["model_name"]) if code != "A" else r["model_name"]
                resp = call(client_for[code], model, r["prompt"], is_groq=(code != "A"))
                provider = "OpenAI" if code == "A" else (getattr(resp, "provider", None) or (getattr(resp, "model_extra", None) or {}).get("provider", ""))
                choice = resp.choices[0]
                w.writerow({
                    "uid": r["uid"], "rep": rep, "topic_id": r["topic_id"], "grade": r["grade"],
                    "subject": r["subject"], "lang": r["lang"], "model_code": code,
                    "model_label": r["model_label"], "requested_model": model, "provider": provider,
                    "returned_model": getattr(resp, "model", ""),
                    "system_fingerprint": getattr(resp, "system_fingerprint", "") or "",
                    "finish_reason": choice.finish_reason,
                    "tokens_in": resp.usage.prompt_tokens if resp.usage else "",
                    "tokens_out": resp.usage.completion_tokens if resp.usage else "",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "response": choice.message.content,
                })
                f.flush()
                print(f"rep {rep}  {i:3d}/{len(rows)}  {r['uid']:10s}  {resp.usage.completion_tokens if resp.usage else '?'} tokens  [{choice.finish_reason}]  via {provider}")
    print(f"\nDone. Results saved to {OUT}.")

if __name__ == "__main__":
    main()
