#!/usr/bin/env python3
from pathlib import Path
import http.server, socketserver, subprocess, sys, webbrowser, threading
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT/'build_library.py')],cwd=ROOT,check=False)
PORT=8000
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store, max-age=0')
        super().end_headers()
with socketserver.TCPServer(('127.0.0.1',PORT),lambda *a,**k:Handler(*a,directory=str(ROOT),**k)) as httpd:
    threading.Timer(.6,lambda:webbrowser.open(f'http://127.0.0.1:{PORT}/')).start()
    print(f'Crystal Lake Comics : http://127.0.0.1:{PORT}/')
    print('Ctrl+C pour arrêter.')
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
