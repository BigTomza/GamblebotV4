import argparse
import http.server
import socketserver
import threading
import urllib.request
import urllib.parse
import urllib.error
import json
import webbrowser
import os

BASE = 'https://api.the-odds-api.com/v4'

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.handle_api_proxy()
        elif self.path == '/test':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            super().do_GET()

    def handle_api_proxy(self):
        """Handle API proxy requests"""
        try:
            api_path = self.path[5:]
            if '?' in api_path:
                api_path, query_string = api_path.split('?', 1)
            else:
                query_string = ""

            base_url = "https://api.the-odds-api.com/v4"
            full_url = f"{base_url}/{api_path}"
            if query_string:
                full_url += f"?{query_string}"

            print(f"🔄 API Proxy: {self.path} → {full_url}")

            headers = {
                'User-Agent': 'Gamblebot/3.0.0 (Local Server)',
                'Accept': 'application/json'
            }

            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
                status = response.status
                print(f"✅ API Response: {status} - {len(data)} bytes")
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            print(f"❌ API HTTP Error: {e.code} - {e.reason}")
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_data = json.dumps({'error': 'API request failed', 'status': e.code, 'message': e.reason}).encode()
            self.wfile.write(error_data)
        except Exception as e:
            print(f"❌ API Proxy Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_data = json.dumps({'error': 'Internal server error', 'message': str(e)}).encode()
            self.wfile.write(error_data)

def get_server(start=8000):
    port = start
    while True:
        try:
            httpd = socketserver.ThreadingTCPServer(('', port), Handler)
            return port, httpd
        except OSError:
            port += 1


def main(test=False):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port, httpd = get_server()
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    if test:
        with urllib.request.urlopen(f'http://localhost:{port}/test') as resp:
            print(resp.read().decode())
        httpd.shutdown()
        return
    url = f'http://localhost:{port}/index.html'
    print(f'Serving on {url}')
    webbrowser.open(url)
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    httpd.shutdown()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    main(test=args.test)
