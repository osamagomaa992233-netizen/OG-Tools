import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from engine.server import Handler

class TestBridge(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  cls.base=f'http://127.0.0.1:{cls.server.server_port}'
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
 def request(self,url,data=None,headers=None):
  req=Request(self.base+url,data=json.dumps(data).encode() if data else None,headers=headers or {},method='POST' if data else 'GET')
  with urlopen(req,timeout=10) as response:return json.loads(response.read().decode())
 def test_01_health(self):self.assertTrue(self.request('/api/health')['ok'])
 def test_02_live_sfx_job(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'sfx.wav'
   data=self.request('/api/jobs',{'tool':'sfx','kind':'click','duration':.1,'output':str(path)},{'Content-Type':'application/json','X-OG-Tools':'local'})
   job=data['id']
   for _ in range(70):
    result=self.request('/api/jobs/'+job)
    if result['status'] in ('done','error'):break
    time.sleep(.1)
   self.assertEqual(result['status'],'done',result)
   self.assertTrue(path.exists())
 def test_03_reject_unauthorized(self):
  with self.assertRaises(HTTPError) as error:
   self.request('/api/jobs',{'tool':'sfx'},{'Content-Type':'application/json'})
  self.assertEqual(error.exception.code,403)
 def test_04_reject_web_origin(self):
  with self.assertRaises(HTTPError) as error:
   self.request('/api/health',headers={'Origin':'https://evil.example'})
  self.assertEqual(error.exception.code,403)
if __name__=='__main__':unittest.main()
