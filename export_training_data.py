"""
export_training_data.py
────────────────────────────────────────────────
Reads your Vishfit AI conversation data from Google Sheets
and exports it as a JSONL file ready for fine-tuning Mistral.

Run: python3 export_training_data.py
Output: vishfit_training_data.jsonl
"""

import json
import csv
import os
from datetime import datetime

# ─── OPTION 1: Export from Google Sheet (CSV) ─────────────────────
# In Google Sheets → File → Download → CSV
# Then set this path:
CSV_FILE = "vishfit_conversations.csv"

# ─── OPTION 2: Use n8n to auto-export (set webhook to write file) ──
# Or run this script on a schedule via cron

SYSTEM_PROMPT = """You are VishFit AI, an elite personal fitness coach and nutritionist.
Give specific, actionable fitness and nutrition advice with exact numbers.
Always motivate and encourage the user."""

def csv_to_jsonl(csv_path: str, output_path: str):
    """Convert Google Sheet CSV export to JSONL training format."""
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        print("   Export your Google Sheet as CSV first.")
        return

    training_samples = []
    skipped = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_msg = row.get("user_message", "").strip()
            ai_reply = row.get("ai_reply", "").strip()

            # Skip empty or very short exchanges
            if len(user_msg) < 5 or len(ai_reply) < 20:
                skipped += 1
                continue

            sample = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": user_msg},
                    {"role": "assistant", "content": ai_reply}
                ]
            }
            training_samples.append(sample)

    # Write JSONL file
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in training_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"✅ Exported {len(training_samples)} training samples")
    print(f"   Skipped {skipped} low-quality rows")
    print(f"   Output: {output_path}")
    print(f"\n📊 Training data quality:")
    print(f"   • < 100 samples  → Basic improvement")
    print(f"   • 100-500        → Noticeable improvement")
    print(f"   • 500-1000       → Significant improvement")
    print(f"   • 1000+          → Expert-level Vishfit AI")

def preview_samples(jsonl_path: str, n: int = 3):
    """Preview first N training samples."""
    print(f"\n👀 Preview of first {n} training samples:\n")
    with open(jsonl_path, "r") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            sample = json.loads(line)
            user = sample["messages"][1]["content"]
            assistant = sample["messages"][2]["content"][:100]
            print(f"Sample {i+1}:")
            print(f"  User:      {user[:80]}")
            print(f"  Assistant: {assistant}...")
            print()

def create_modelfile(jsonl_path: str):
    """Create an Ollama Modelfile for fine-tuning."""
    modelfile_content = f"""# Vishfit AI — Custom Fine-tuned Model
# Generated: {datetime.now().strftime('%Y-%m-%d')}

FROM mistral

SYSTEM \"\"\"{SYSTEM_PROMPT}\"\"\"

# Training data: {jsonl_path}
# To use this model: ollama create vishfit-pro -f Modelfile
# Then update MODEL_NAME = "vishfit-pro" in main.py
"""
    with open("Modelfile", "w") as f:
        f.write(modelfile_content)
    print("✅ Modelfile created → run: ollama create vishfit-pro -f Modelfile")

if __name__ == "__main__":
    output = "vishfit_training_data.jsonl"
    
    print("🏋️  Vishfit AI — Training Data Exporter")
    print("=" * 45)
    
    csv_to_jsonl(CSV_FILE, output)
    
    if os.path.exists(output):
        preview_samples(output)
        create_modelfile(output)
        
        print("\n🚀 Next steps:")
        print("   1. Use vishfit_training_data.jsonl for fine-tuning")
        print("   2. Upload to HuggingFace / Unsloth for full fine-tuning")
        print("   3. Or use Modelfile for basic Ollama customization")