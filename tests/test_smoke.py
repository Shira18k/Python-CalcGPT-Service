# test_smoke.py
import time, threading

def start_server():
    import server
    server.serve("127.0.0.1", 5599, 16)

def test_calc_and_cache():
    t = threading.Thread(target=start_server, daemon=True); t.start()
    time.sleep(0.3)
    import client
    r1 = client.request("127.0.0.1", 5599, {"mode":"calc","data":{"expr":"sin(0)"},"options":{"cache":True}})
    assert r1["ok"] and abs(r1["result"] - 0.0) < 1e-9
    r2 = client.request("127.0.0.1", 5599, {"mode":"calc","data":{"expr":"sin(0)"},"options":{"cache":True}})
    assert r2["meta"]["from_cache"] is True

if __name__ == "__main__":
    test_calc_and_cache()
    print("OK")
