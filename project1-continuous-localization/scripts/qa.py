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
    tpl = load(PROMPTS / "qa_prompt.txt")

    for lang in langs:
        tgt = json.loads((OUT / f"strings.{lang}.json").read_text(encoding="utf-8"))
        prompt = tpl\
            .replace("{{target_lang}}", lang)\
            .replace("{{style_guide}}", style)\
            .replace("{{glossary_json}}", json.dumps(glossary, ensure_ascii=False))\
            .replace("{{length_limits_json}}", json.dumps(meta.get("length_limits", {}), ensure_ascii=False))\
            .replace("{{source_json}}", json.dumps(en, ensure_ascii=False))\
            .replace("{{target_json}}", json.dumps(tgt, ensure_ascii=False))

        resp = model.generate_content([prompt])
        raw = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        report = json.loads(raw)
        (OUT / f"qa_report.{lang}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote outputs/qa_report.{lang}.json")

if __name__ == "__main__":
    main()
