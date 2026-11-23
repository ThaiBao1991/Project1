import json
with open(r'C:\Users\games\.gemini\antigravity\brain\907d56c7-d8f9-42ac-b4e4-4334005247a1\.system_generated\logs\transcript_full.jsonl', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx in range(290, 296):
            print(f"=== STEP {idx} ===")
            print('CONTENT:', str(obj.get('content'))[:400])
            if obj.get('tool_calls'):
                print('TOOLS:', obj.get('tool_calls'))
