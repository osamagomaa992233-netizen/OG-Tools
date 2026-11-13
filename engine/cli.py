"""Automation/CI command line usage: python -m engine.cli tool --json file.json"""
import argparse,json
from pathlib import Path
from .core import execute

def main():
    p=argparse.ArgumentParser(description='Run an OG Tools job locally')
    p.add_argument('tool');p.add_argument('--json',dest='json_file')
    p.add_argument('--source');p.add_argument('--output');p.add_argument('--text')
    p.add_argument('--motion');p.add_argument('--style');p.add_argument('--format')
    args=p.parse_args()
    data=json.loads(Path(args.json_file).read_text(encoding='utf8')) if args.json_file else {}
    data.update({k:v for k,v in vars(args).items() if k in ('source','output','text','motion','style','format') and v is not None})
    data['tool']=args.tool
    print(json.dumps(execute(data),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
