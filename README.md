\# EX2 — Application Layer Lab (Python 3.13+)



This exercise teaches the basics of TCP sockets in Python and a simple app-layer protocol over TCP using \*\*line-delimited JSON\*\*.



\## Components

\- `server.py`: TCP server that accepts one-line JSON requests and returns one-line JSON responses.

&nbsp; - `mode="calc"`: evaluate a math expression safely (no `eval`).

&nbsp; - `mode="gpt"`: send a prompt to GPT (stub by default; can be replaced with a real API call).

&nbsp; - Built-in LRU cache for responses.

\- `client.py`: simple client for sending requests to the server.

\- `proxy.py` (optional challenge): transparent TCP proxy you can extend (e.g., logging or local cache).

\- `tests/test\_smoke.py`: tiny smoke test.

\- `requirements.txt`: dependencies (only needed if you choose to enable real GPT calls).



\## Quick Start

```bash

pip install -r requirements.txt   # optional unless you enable GPT real calls

python server.py --host 127.0.0.1 --port 5555



\# Calculate:

python client.py --host 127.0.0.1 --port 5555 --mode calc --expr "sin(max(2,3\*4,5)/7)\*3"



\# GPT (stub by default):

python client.py --host 127.0.0.1 --port 5555 --mode gpt --prompt "Summarize Newton in 3 bullet points"



\## Quick Start with Proxy

python proxy.py --listen-port 5554 --server-port 5555

python client.py --host 127.0.0.1 --port 5554 --mode calc --expr "sqrt(16)"



