"""PyInstaller entry point for local OG Tools engine on Windows."""
import sys
from pathlib import Path

def main():
    # Bundled resources, if any, are looked up alongside the frozen EXE.
    if getattr(sys, 'frozen', False):
        exe_dir=Path(sys.executable).parent
        import os
        os.environ['PATH']=str(exe_dir)+os.pathsep+os.environ.get('PATH','')
    from engine.server import main as serve
    serve()

if __name__=='__main__':
    main()
