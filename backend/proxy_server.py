#!/usr/bin/env python3
"""
Simple proxy server that serves the frontend and forwards API calls to the backend
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
from pathlib import Path

# Configuration
FRONTEND_DIR = os.path.abspath("../cursor-extension/dist")
BACKEND_URL = "http://localhost:8000"
PORT = 3000

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Check if this is an API call
        if self.path.startswith('/api/'):
            # Forward to backend
            try:
                backend_url = f"{BACKEND_URL}{self.path}"
                print(f"Proxying GET {self.path} -> {backend_url}")
                
                with urllib.request.urlopen(backend_url) as response:
                    content = response.read()
                    self.send_response(response.status)
                    for header, value in response.getheaders():
                        self.send_header(header, value)
                    self.end_headers()
                    self.wfile.write(content)
                return
            except Exception as e:
                print(f"Error proxying to backend: {e}")
                self.send_error(500, f"Backend error: {e}")
                return
        
        # Serve static files if they exist
        request_path = self.path.lstrip('/')
        
        # Handle root path specially
        if not request_path:
            print(f"[DEBUG] Serving index.html for root path: {self.path}")
            try:
                with open(os.path.join(FRONTEND_DIR, 'index.html'), 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"Error serving index.html: {e}")
                self.send_error(500, f"Error serving index.html: {e}")
                return
        
        static_path = os.path.join(FRONTEND_DIR, request_path)
        print(f"[DEBUG] Requested path: {self.path}, Resolved static_path: {static_path}, Exists: {os.path.isfile(static_path)}")
        
        if os.path.isfile(static_path):
            # Serve the file directly
            try:
                with open(static_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type based on file extension
                if static_path.endswith('.js'):
                    content_type = 'application/javascript'
                elif static_path.endswith('.css'):
                    content_type = 'text/css'
                elif static_path.endswith('.html'):
                    content_type = 'text/html'
                elif static_path.endswith('.json'):
                    content_type = 'application/json'
                else:
                    content_type = 'application/octet-stream'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"Error serving static file {static_path}: {e}")
                self.send_error(500, f"Error serving file: {e}")
                return
        
        # If the request is for a file (has an extension) but doesn't exist, return 404
        if '.' in self.path.split('/')[-1]:
            print(f"[DEBUG] 404 for missing static file: {self.path}")
            self.send_error(404, "File not found")
            return
        
        # Otherwise, serve index.html for SPA routing
        print(f"[DEBUG] Serving index.html for SPA route: {self.path}")
        try:
            with open(os.path.join(FRONTEND_DIR, 'index.html'), 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
            return
        except Exception as e:
            print(f"Error serving index.html for SPA route: {e}")
            self.send_error(500, f"Error serving index.html: {e}")
            return
    
    def do_POST(self):
        # Check if this is an API call
        if self.path.startswith('/api/'):
            # Forward to backend
            try:
                backend_url = f"{BACKEND_URL}{self.path}"
                print(f"Proxying POST {self.path} -> {backend_url}")
                
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Create request to backend
                req = urllib.request.Request(backend_url, data=post_data)
                req.add_header('Content-Type', self.headers.get('Content-Type', 'application/json'))
                
                with urllib.request.urlopen(req) as response:
                    self.send_response(response.status)
                    for header, value in response.getheaders():
                        self.send_header(header, value)
                    self.end_headers()
                    self.wfile.write(response.read())
                return
            except Exception as e:
                print(f"Error proxying to backend: {e}")
                self.send_error(502, f"Backend error: {e}")
                return
        
        # Default POST handling
        super().do_POST()

def main():
    # Check if frontend directory exists
    frontend_path = Path(FRONTEND_DIR).resolve()
    if not frontend_path.exists():
        print(f"Frontend directory not found: {frontend_path}")
        sys.exit(1)
    
    print(f"Serving frontend from: {frontend_path}")
    print(f"Proxying API calls to: {BACKEND_URL}")
    print(f"Server running on: http://localhost:{PORT}")
    
    # Create server
    with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"Proxy server started on port {PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    main() 