"""
TechPack AI Extractor
Garment tech pack ছবি/PDF-এর পেজ আপলোড করলে Claude vision দিয়ে
স্ট্রাকচার্ড ডাটা (JSON, Excel) বের করে দেয়।

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=your_key      (Windows: set ANTHROPIC_API_KEY=your_key)
    streamlit run app.py
"""
import base64
import io
import json
import os

import anthropic
import pandas as pd
import streamlit as st

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert garment technical designer reading a tech pack page.
Extract ALL visible information and return ONLY valid JSON (no markdown fences) in this schema:
{
  "style_info": {"style_no": "", "style_name": "", "buyer": "", "season": "", "category": "",
                 "fabric_description": "", "colorways": [], "size_range": "", "date": "", "revision": ""},
  "measurements": [{"point_of_measure": "", "code": "", "tolerance": "", "sizes": {"S": "", "M": "", "L": ""}}],
  "bill_of_materials": [{"type": "fabric|trim|label|packaging|thread|other", "item": "", "description": "",
                         "color": "", "placement": "", "consumption": "", "supplier": ""}],
  "construction_details": [{"area": "", "stitch_type": "", "spi": "", "notes": ""}],
  "labels_and_packaging": [],
  "special_notes": []
}
Rules: use "" or [] when a field is not on the page. Never invent values. Keep units as written
(cm, inch, yards...). If text is unreadable, write "UNREADABLE" for that value."""


def to_b64(file) -> tuple[str, str]:
    data = file.getvalue()
    media = file.type or "image/png"
    return base64.standard_b64encode(data).decode(), media


def extract(client, files, extra_hint: str) -> dict:
    content = []
    for f in files:
        b64, media = to_b64(f)
        content.append({"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}})
    content.append({"type": "text", "text": "Extract the tech pack data from these page(s). " + extra_hint})
    resp = client.messages.create(
        model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def to_excel(data: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame([data.get("style_info", {})]).to_excel(xw, "Style Info", index=False)
        m = [{**{k: v for k, v in r.items() if k != "sizes"}, **r.get("sizes", {})}
             for r in data.get("measurements", [])]
        pd.DataFrame(m).to_excel(xw, "Measurements", index=False)
        pd.DataFrame(data.get("bill_of_materials", [])).to_excel(xw, "BOM", index=False)
        pd.DataFrame(data.get("construction_details", [])).to_excel(xw, "Construction", index=False)
    return buf.getvalue()


st.set_page_config(page_title="TechPack AI Extractor", page_icon="🧵", layout="wide")
st.title("🧵 TechPack AI Extractor")
st.caption("Garment tech pack-এর ছবি আপলোড করুন → structured data পান (JSON / Excel)")

api_key = os.getenv("ANTHROPIC_API_KEY") or st.sidebar.text_input("Anthropic API Key", type="password")
hint = st.sidebar.text_area("অতিরিক্ত নির্দেশ (optional)", placeholder="যেমন: শুধু measurement table বের করো")
files = st.file_uploader("Tech pack page(s) (PNG/JPG/WEBP)", type=["png", "jpg", "jpeg", "webp"],
                         accept_multiple_files=True)

if files:
    cols = st.columns(min(len(files), 4))
    for c, f in zip(cols, files):
        c.image(f, caption=f.name, use_container_width=True)

if st.button("Extract Data", type="primary", disabled=not (files and api_key)):
    with st.spinner("AI ছবি পড়ছে..."):
        try:
            st.session_state["result"] = extract(anthropic.Anthropic(api_key=api_key), files, hint)
        except json.JSONDecodeError:
            st.error("AI-এর উত্তর JSON হিসেবে পার্স করা যায়নি, আবার চেষ্টা করুন।")
        except Exception as e:
            st.error(f"Error: {e}")

data = st.session_state.get("result")
if data:
    t1, t2, t3, t4, t5 = st.tabs(["Style Info", "Measurements", "BOM", "Construction", "Raw JSON"])
    with t1:
        st.json(data.get("style_info", {}))
    with t2:
        rows = [{**{k: v for k, v in r.items() if k != "sizes"}, **r.get("sizes", {})}
                for r in data.get("measurements", [])]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    with t3:
        st.dataframe(pd.DataFrame(data.get("bill_of_materials", [])), use_container_width=True)
    with t4:
        st.dataframe(pd.DataFrame(data.get("construction_details", [])), use_container_width=True)
    with t5:
        st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")

    d1, d2 = st.columns(2)
    d1.download_button("⬇ JSON", json.dumps(data, indent=2, ensure_ascii=False), "techpack.json")
    d2.download_button("⬇ Excel", to_excel(data), "techpack.xlsx")
    st.warning("AI output সবসময় মূল tech pack-এর সাথে মিলিয়ে নিন, বিশেষ করে measurement-এর সংখ্যা।")
