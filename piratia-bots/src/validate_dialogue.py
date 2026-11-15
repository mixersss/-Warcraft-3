"""Validate all facts/examples/templates and count distinct meaningful reply data."""
import json
from pathlib import Path
from dialogue_data import DialogueData

def main():
    data=DialogueData(Path(__file__).resolve().parents[1]/'assets');errors=[]
    for row in data.rows:
        for text in row['examples']:
            got=data.recognizer.recognize(text).name
            if got!=row['id']:errors.append((row['id'],got))
    result={**data.summary(),'input_examples':sum(len(r['examples']) for r in data.rows),'recognition_mismatches':len(errors),'permutation_padding_counted':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
