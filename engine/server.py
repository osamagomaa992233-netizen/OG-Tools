"""Local-only bridge from Premiere UXP to the Python media engine.
No paid API, telemetry, login, remote listener or shell execution.
"""
import argparse
import json
import threading
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .core import execute,TOOLS

JOBS={};LOCK=threading.Lock()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):pass
    def _origin_allowed(self):
        origin=self.headers.get('Origin','')
        # Adobe UXP's runtime origin varies by host version; fetch often has no Origin.
        return not origin or origin=='null' or origin.startswith(('uxp://','http://127.0.0.1:','http://localhost:'))
    def _headers(self,code=200):
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        origin=self.headers.get('Origin','')
        if self._origin_allowed():
            self.send_header('Access-Control-Allow-Origin',origin if origin and origin!='null' else '*')
        self.send_header('Access-Control-Allow-Headers','Content-Type, X-OG-Tools')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Cache-Control','no-store')
        self.end_headers()
    def answer(self,data,code=200):
        self._headers(code);self.wfile.write(json.dumps(data,ensure_ascii=False,default=str).encode('utf8'))
    def do_OPTIONS(self):
        if not self._origin_allowed():self.answer({'error':'Origin denied'},403);return
        self._headers(204)
    def do_GET(self):
        if not self._origin_allowed():self.answer({'error':'Origin denied'},403);return
        if self.path=='/api/health':
            import importlib.util,shutil
            have=lambda name:importlib.util.find_spec(name) is not None
            self.answer({'ok':True,'name':'OG Tools','version':'0.9.0','location':'localhost only',
               'capabilities':{'ffmpeg':bool(shutil.which('ffmpeg')),'ffprobe':bool(shutil.which('ffprobe')),
               'pillow':have('PIL'),'whisper':have('faster_whisper'),'rembg':have('rembg'),
               'opencv':have('cv2'),'ytdlp':bool(shutil.which('yt-dlp'))}});return
        if self.path=='/api/tools':self.answer({'tools':TOOLS});return
        if self.path.startswith('/api/jobs/'):
            job_id=self.path.split('/')[-1]
            with LOCK:task=JOBS.get(job_id)
            self.answer(task if task else {'error':'Unknown job'},200 if task else 404);return
        self.answer({'error':'Not found'},404)
    def do_POST(self):
        if not self._origin_allowed():self.answer({'error':'Origin denied'},403);return
        if self.path!='/api/jobs':self.answer({'error':'Not found'},404);return
        if self.headers.get('X-OG-Tools')!='local':self.answer({'error':'OG Tools header required'},403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<65536:raise ValueError('Invalid job body')
            spec=json.loads(self.rfile.read(size))
            if not isinstance(spec,dict):raise ValueError('Expected object')
        except Exception as e:self.answer({'error':str(e)},400);return
        job_id=str(uuid.uuid4())
        with LOCK:
            if len(JOBS)>300:
                for key in list(JOBS)[:100]:JOBS.pop(key,None)
            JOBS[job_id]={'id':job_id,'status':'queued','tool':spec.get('tool')}
        def work():
            with LOCK:JOBS[job_id]['status']='running'
            try:
                result=execute(spec)
                with LOCK:JOBS[job_id].update(status='done',result=result)
            except Exception as exc:
                with LOCK:JOBS[job_id].update(status='error',error=str(exc))
                print('OG Tools job failed:',type(exc).__name__,str(exc),flush=True)
        threading.Thread(target=work,name='OGJob-'+job_id[:7],daemon=True).start()
        self.answer({'id':job_id,'status':'queued'},202)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8734)
    args=parser.parse_args()
    host='127.0.0.1';http=ThreadingHTTPServer((host,args.port),Handler)
    print(f'OG Tools local engine ready: http://{host}:{args.port}/api/health',flush=True)
    try:http.serve_forever()
    except KeyboardInterrupt:pass
    finally:http.server_close()
if __name__=='__main__':main()
