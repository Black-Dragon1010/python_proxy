from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_GET(self, body=True):
        try:
            # Parse request
            hostname = 'preprod.bank.com'
            url = 'https://{}{}'.format(hostname, self.path)
            req_header = self.parse_headers()

            # Call the target service
            resp = requests.get(url, headers=req_header, verify=False)

            # Respond with the requested data
            self.send_response(resp.status_code)
            self.send_resp_headers(resp.headers)
            self.wfile.write(resp.content)
            return
        finally:
            self.finish()

if __name__ == '__main__':
    server_address = ('127.0.0.1', 8081)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print('http server is running')
    httpd.serve_forever()