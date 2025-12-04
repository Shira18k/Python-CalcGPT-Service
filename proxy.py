# proxy.py
import argparse, socket, threading, json

def pipe(src, dst):
    """Bi-directional byte piping helper."""
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try: dst.shutdown(socket.SHUT_WR)
        except Exception: pass

def main():
    ap = argparse.ArgumentParser(description="Transparent TCP proxy (optional)")
    ap.add_argument("--listen-host", default="127.0.0.1")
    ap.add_argument("--listen-port", type=int, default=5554)
    ap.add_argument("--server-host", default="127.0.0.1")
    ap.add_argument("--server-port", type=int, default=5555)
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.listen_host, args.listen_port))
        s.listen(16)
        print(f"[proxy] {args.listen_host}:{args.listen_port} -> {args.server_host}:{args.server_port}")
        while True:
            c, addr = s.accept()
            threading.Thread(target=handle, args=(c, args.server_host, args.server_port), daemon=True).start()

def handle(c, sh, sp):
    with c:
        try:
            with socket.create_connection((sh, sp)) as s:
                t1 = threading.Thread(target=pipe, args=(c, s), daemon=True)
                t2 = threading.Thread(target=pipe, args=(s, c), daemon=True)
                t1.start(); t2.start()
                t1.join(); t2.join()
        except Exception as e:
            try: c.sendall((json.dumps({"ok": False, "error": f"Proxy error: {e}"})+"\n").encode("utf-8"))
            except Exception: pass

if __name__ == "__main__":
    main()
