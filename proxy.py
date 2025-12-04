# proxy.py
""

import argparse, socket, json, time, threading, math, os, ast, operator, collections

from collections import OrderedDict
from server import handle_client

#!
FAULT_RATE = 0.1       # 10% chance of dropping packets
MIN_LATENCY = 0.0      # Minimum latency in seconds
MAX_LATENCY = 0.5      # Maximum latency in seconds


class LRUCache:
    def __init__(self, capacity = 128):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self.cache.move_to_end(key)
            if len(self.cache) > self.capacity :
                self.cache.popitem(last=False)


# def pipe(src, dst): #read from board
#
#     #! add dir for print -the fun for getting the inf
#     """Bi-directional byte piping helper."""
#     try:
#         while True:
#             data = src.recv(4096)
#             if not data:
#                 break
#             dst.sendall(data)
#     except Exception as e:
#             print(f"[proxy] server not responding: {e}")
#             #?
#     finally:
#         try:
#             dst.shutdown(socket.SHUT_WR)
#         except:
#             pass
def _recv_json_line(sock: socket.socket) -> dict:
    """Read a full JSON line (ending with \n) from the socket."""
    raw = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionResetError("Client closed connection")
        raw += chunk
        if b"\n" in raw:
            line, _, _ = raw.partition(b"\n")
            return json.loads(line.decode("utf-8"))


#! - the part "proxy"
def proxy_server(host: str, port: int, server_host, server_port):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(16)
        print(f"[Proxy] listening on {host}:{port}")
        print(f"[proxy] Forwarding to {server_host}:{server_port}")
        while True:
            # see if that what accepted
            client_socket, addr = s.accept()
            print(f"[proxy] New client: {addr}")
            # what with the cache - important...
            threading.Thread(target=handle, args=(client_socket, server_host, server_port), daemon=True).start()


def handle(client_socket, server_host, server_port, cache: LRUCache): # the name mmore clear
    with client_socket:
        while True:
            started = time.time()
            try:
                #read the msg from client
                msg = _recv_json_line(client_socket)
            except (ConnectionResetError, EOFError):
                print("[proxy] Client closed connection.")
                break
            except Exception as e:
                print(f"[proxy] Error reading client request: {e}")
                break
            cache_key = json.dumps(msg, sort_keys=True)
            options = msg.get("options", {})
            use_cache = bool(options.get("cache", True))
            #if found the msg in cache
            if use_cache:
                hit = cache.get(cache_key)
                if hit is not None:
                    took = int((time.time() - started) * 1000)
                    resp = {"ok": True, "result": hit, "meta": {"from_cache": True, "took_ms": took}}
                    client_socket.sendall((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                    print(f"[proxy] Served from cache: {cache_key}")
                    continue
            try:
            # connect to server(not found in cache)
                with socket.create_connection((server_host, server_port), timeout=10) as s:
                    request_data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
                    s.sendall(request_data)
                    server_resp = _recv_json_line(s)

                    if server_resp.get("ok") and use_cache:
                        cache.set(cache_key, server_resp.get("result"))
                        print(f"[proxy] Saved to cache: {cache_key}")

                    took = int((time.time() - started) * 1000)
                    if "meta" in server_resp:
                        server_resp["meta"]["proxy_took_ms"] = took
                    else:
                        server_resp["meta"] = {"proxy_took_ms": took}

                    client_socket.sendall((json.dumps(server_resp, ensure_ascii=False) + "\n").encode("utf-8"))
                    continue

            #the server close/ unavailable
            except ConnectionRefusedError:
                took = int((time.time() - started) * 1000)
                resp = {"ok": False, "error": "Server unavailable. Cache miss."}
                client_socket.sendall((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                print(f"[proxy] Server is down. Cache miss for: {cache_key}")
                continue

            except Exception as e:
                took = int((time.time() - started) * 1000)
                resp = {"ok": False, "error": f"Proxy communication error: {e}"}
                client_socket.sendall((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                continue

def main():
    ap = argparse.ArgumentParser(description="Transparent TCP proxy (optional)")
    ap.add_argument("--listen-host", default="127.0.0.1")
    ap.add_argument("--listen-port", type=int, default=5554)
    ap.add_argument("--server-host", default="127.0.0.1")
    ap.add_argument("--server-port", type=int, default=5555)
    ap.add_argument("--cache-size", type=int, default=128)# size of cache

    #read the args
    args = ap.parse_args()
    # copy of cache
    cache = LRUCache(args.cache_size)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.listen_host, args.listen_port))
        s.listen(16)
        print(f"[proxy] {args.listen_host}:{args.listen_port} -> {args.server_host}:{args.server_port}")
        while True:
            c, addr = s.accept()
            threading.Thread(target=handle, args=(c, args.server_host, args.server_port,cache), daemon=True).start()

if __name__ == "__main__":
    main()
