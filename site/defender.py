from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

PORT = 8443 
PAGE = "index.html" 

class MaintenanceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Ici tu peux mettre un contrôle IP ou authentification
        # Exemple simple : limiter l'accès à localhost
        if self.client_address[0] not in ('127.0.0.1','::1'):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Acces refuse")
            return
        
        self.path = PAGE
        return super().do_GET()

httpd = HTTPServer(('0.0.0.0', PORT), MaintenanceHandler)

print(f"Server running on https://localhost:{PORT}")
httpd.serve_forever()
