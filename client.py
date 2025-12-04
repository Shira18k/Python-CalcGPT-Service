# client.py
import argparse, socket, json, sys

HOST = '127.0.0.1'
PORT = 5555

def request(host: str, port: int, payload: dict) -> dict:
    """Send a single JSON-line request and return a single JSON-line response."""
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=5) as s:
        s.sendall(data)
        buff = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buff += chunk
            if b"\n" in buff:
                line, _, _ = buff.partition(b"\n")
                return json.loads(line.decode("utf-8"))
    return {"ok": False, "error": "No response"}


def run_client_interactive(s: socket.socket):
    while True:
        # הצגת האפשרויות:
        print("\n which mode? ")
        print("1. Calc ")
        print("2. GPT ")
        print("3. EXIT ")

        choice = input("your choice: ")

        if choice == '3':
            break  # יציאה מהלולאה וסגירת החיבור

        elif choice == '1':
            mode = "calc"
            # קבלת הקלט החופשי עבור ה-expr
            print("\n which expression?")
            print("1. 1+1+1*100")
            print("2. 2^6")
            print("3. 4^0.5")
            print("4. free choice")
            print("5. EXIT")

            choice_calc = input("your choice: ")

            user_expr = None
            if choice_calc == '5':
                break

            if choice_calc == '1':
                user_expr = "1+1+1*100"

            if choice_calc == '2':
                user_expr = "2**6"
            if choice_calc == '3':
                user_expr = "4**0.5"
            if choice_calc == '4':

                user_expr = input("your choice: ")

            if user_expr is None:
                print("Invalid choice or empty expression.")
                continue

            data_payload = {"expr": user_expr}
            msg = {"mode": mode, "data": data_payload}
            send_and_receive(s, msg)

        elif choice == '2':
            mode = "gpt"
            user_prompt = input("\n What is your q: ")

            data_payload = {"prompt": user_prompt}
            msg = {"mode": mode, "data": data_payload}


            send_and_receive(s, msg)

        else:
            print("illegal , try again:( ")
            continue


def send_and_receive(s: socket.socket, msg: dict):
    request_data = json.dumps(msg) + "\n"

    print(f"[client] Sending: {request_data.strip()}")
    s.sendall(request_data.encode('utf-8'))

    buffer = b""
    while True:
        try:
            chunk = s.recv(1024)
        except ConnectionResetError:
            print("[client] Connection forcibly closed by the server.")
            return None

        if not chunk:
            print("[client] Server closed the connection unexpectedly.")
            return None

        buffer += chunk

        if b'\n' in buffer:
            line, _, buffer = buffer.partition(b'\n')
            break

    try:
        response_json = line.decode('utf-8')
        response_dict = json.loads(response_json)

        print(f"[client] Received response:")
        print(json.dumps(response_dict, indent=4, ensure_ascii=False))

        return response_dict

    except json.JSONDecodeError:
        print(f"[client] ERROR: Failed to decode JSON response: {line}")
        return None
    except Exception as e:
        print(f"[client] An unexpected error occurred: {e}")
        return None



def main():
    ap = argparse.ArgumentParser(description="Client (calc/gpt over JSON TCP)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--mode", choices=["calc", "gpt"], required=True)
    ap.add_argument("--expr", help="Expression for mode=calc")
    ap.add_argument("--prompt", help="Prompt for mode=gpt")
    ap.add_argument("--no-cache", action="store_true", help="Disable caching")
    args = ap.parse_args()

    if args.mode == "calc":
        if not args.expr:
            print("Missing --expr", file=sys.stderr); sys.exit(2)
        payload = {"mode": "calc", "data": {"expr": args.expr}, "options": {"cache": not args.no_cache}}
    else:
        if not args.prompt:
            print("Missing --prompt", file=sys.stderr); sys.exit(2)
        payload = {"mode": "gpt", "data": {"prompt": args.prompt}, "options": {"cache": not args.no_cache}}

    resp = request(args.host, args.port, payload)
    print(json.dumps(resp, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"[client] Connected to {HOST}:{PORT}")

            run_client_interactive(s)  # העבירי את הסוקט!

        except ConnectionRefusedError:
            print("Error: Could not connect to the server. Is server.py running?")
