import os, json
from pathlib import Path
import google.generativeai as genai

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROMPTS = ROOT / "prompts"
OUT = ROOT / "outputs"

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def load(p): return Path(p).read_text(encoding="utf-8")
def jl(p): return json.loads(load(p))

def main():
    langs = jl(DATA / "languages.json")
    en = jl(DATA / "strings/en.json")
    meta = jl(DATA / "strings/metadata.json")
    glossary = jl(DATA / "glossary/en.json")
    style = load(DATA / "style_guide.md")
    tpl = load(PROMPTS / "translate_prompt.txt")

    for lang in langs:
        prompt = tpl\
            .replace("{{target_lang}}", lang)\
            .replace("{{style_guide}}", style)\
            .replace("{{glossary_json}}", json.dumps(glossary, ensure_ascii=False))\
            .replace("{{length_limits_json}}", json.dumps(meta.get("length_limits", {}), ensure_ascii=False))\
            .replace("{{strings_json}}", json.dumps(en, ensure_ascii=False))
        resp = model.generate_content([prompt])
        raw = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        out = json.loads(raw)

        # overlay human feedback corrections if present
        fb = ROOT / "feedback" / "edits.jsonl"
        if fb.exists():
            corr = {}
            for line in fb.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                rec = json.loads(line)
                if rec.get("lang")==lang and rec.get("key") and rec.get("new"):
                    corr[rec["key"]] = rec["new"]
            for k,v in corr.items():
                if k in out: out[k] = v

        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"strings.{lang}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote outputs/strings.{lang}.json")

if __name__ == "__main__":
    main()
