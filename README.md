# 🧵 TechPack AI Extractor

Garment tech pack-এর ছবি থেকে Claude vision দিয়ে structured data (style info, measurement chart, BOM, construction) বের করার টুল।

## Setup
```bash
pip install streamlit anthropic pandas openpyxl
export ANTHROPIC_API_KEY=your_key   # Windows: set ANTHROPIC_API_KEY=your_key
streamlit run app.py
```

## Features
- একাধিক পেজ একসাথে আপলোড
- Style info, Measurements (size-wise), BOM, Construction আলাদা ট্যাবে
- JSON ও Excel ডাউনলোড
- Optional extra instruction (যেমন: "শুধু BOM বের করো")

## Tech
Python, Streamlit, Anthropic API (vision), pandas

## Limitation
AI ভুল পড়তে পারে (বিশেষ করে ঝাপসা সংখ্যা) — মূল ফাইলের সাথে যাচাই করুন।

## Ideas for improvement
- PDF সাপোর্ট, বাল্ক প্রসেসিং, Google Sheets এক্সপোর্ট, validation rules
