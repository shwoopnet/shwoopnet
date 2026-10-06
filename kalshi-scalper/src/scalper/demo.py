"""Kalshi DEMO trading: signed requests, a balance read, one tiny resting order, a cancel,
and the duplicate client_order_id test. DEMO ONLY, by construction:

- The host is a constant. There is no flag, variable or argument that points this at the
  real exchange, and every request is checked against the demo host list before it is sent.
- An order is at most MAX_COUNT contracts at no more than MAX_PRICE, so a test order rests
  far below the market and cannot fill.
- The private key is read from a file on THIS machine and is never printed, logged or sent
  anywhere but into the signature. Keep it out of git and out of chat.

Run it on the machine that holds the demo key (see the README, "Demo trading"):

    export KALSHI_DEMO_KEY_ID=...            # the API key id from the demo site
    export KALSHI_DEMO_KEY_FILE=~/.kalshi/demo_private.pem
    python3 -m scalper.demo balance
    python3 -m scalper.demo order            # one contract at 1c, rests, cancelled for you
    python3 -m scalper.demo dup              # the same client_order_id twice, then cancels

Needs the `cryptography` package (`pip3 install cryptography`).
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

DEMO_BASE = "https://external-api.demo.kalshi.co/trade-api/v2"
DEMO_HOSTS = ("external-api.demo.kalshi.co", "demo-api.kalshi.co")
API_ROOT = "/trade-api/v2"
MAX_COUNT = 5
MAX_PRICE = 0.05
SERIES = "KXBTC15M"


class NotDemo(Exception):
    pass


def assert_demo(url: str) -> None:
    host = urllib.parse.urlparse(url).hostname or ""
    if urllib.parse.urlparse(url).scheme != "https" or host not in DEMO_HOSTS:
        raise NotDemo(f"refusing to send a request to {host or url!r}: this tool is demo only")


def sign_request(private_key, timestamp: str, method: str, path: str) -> str:
    """Kalshi's scheme: sign timestamp + METHOD + the full path from the API root, WITHOUT the
    query string. RSA keys use PSS with SHA-256 and a salt as long as the digest; Ed25519 signs
    the message as is. Returns the base64 signature."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    message = f"{timestamp}{method}{path.split('?')[0]}".encode("utf-8")
    if isinstance(private_key, Ed25519PrivateKey):
        sig = private_key.sign(message)
    else:
        sig = private_key.sign(message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
                               hashes.SHA256())
    return base64.b64encode(sig).decode("utf-8")


def load_key(path: str):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    with open(os.path.expanduser(path), "rb") as f:
        return load_pem_private_key(f.read(), password=None)


def auth_headers(key_id: str, private_key, method: str, path: str, now_ms: int | None = None) -> dict:
    ts = str(now_ms if now_ms is not None else int(time.time() * 1000))
    return {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": sign_request(private_key, ts, method, path),
            "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "shwoopnet-demo/1.0"}


def request(method: str, path: str, *, key_id: str | None = None, key=None, params: dict | None = None,
            body: dict | None = None, opener=None):
    """One request to the demo API. path is relative to the API root ('/portfolio/balance').
    Signed when a key is given. Returns (status, parsed json or text). Never raises on an HTTP
    error status: the caller prints what the exchange said."""
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    url = DEMO_BASE + path + query
    assert_demo(url)
    headers = auth_headers(key_id, key, method, API_ROOT + path) if key is not None else {"Accept": "application/json", "User-Agent": "shwoopnet-demo/1.0"}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with (opener or urllib.request.urlopen)(req, timeout=20) as r:
            raw, status = r.read().decode("utf-8"), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode("utf-8", "replace"), e.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def order_body(ticker: str, count: int, price: float, client_order_id: str, exchange_index: int | None = None) -> dict:
    """A resting buy of YES. Refuses anything that could be more than a tiny test."""
    if not (1 <= count <= MAX_COUNT):
        raise ValueError(f"demo test orders are 1 to {MAX_COUNT} contracts, got {count}")
    if not (0 < price <= MAX_PRICE):
        raise ValueError(f"demo test orders rest at {MAX_PRICE:.2f} or less, got {price}")
    body = {"ticker": ticker, "side": "bid", "count": str(count), "price": f"{price:.2f}",
            "time_in_force": "good_till_canceled", "self_trade_prevention_type": "taker_at_cross",
            "client_order_id": client_order_id}
    if exchange_index is not None:
        body["exchange_index"] = exchange_index
    return body


def pick_market(opener=None) -> dict:
    """An open Bitcoin demo market with at least 5 minutes left (public read, no key)."""
    status, d = request("GET", "/markets", params={"series_ticker": SERIES, "status": "open", "limit": 10}, opener=opener)
    if status != 200 or not isinstance(d, dict):
        raise RuntimeError(f"could not list demo markets: HTTP {status}")
    now = time.time()
    for m in d.get("markets", []):
        close = datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp()
        if close - now > 300:
            return m
    raise RuntimeError("no demo market with 5+ minutes left; try again in a minute")


def credentials():
    key_id, path = os.environ.get("KALSHI_DEMO_KEY_ID"), os.environ.get("KALSHI_DEMO_KEY_FILE")
    if not key_id or not path:
        sys.exit("Set KALSHI_DEMO_KEY_ID and KALSHI_DEMO_KEY_FILE (path to the demo private key). See the README.")
    return key_id, load_key(path)


def show(label: str, status: int, body) -> None:
    print(f"{label}: HTTP {status}")
    print("  " + (json.dumps(body, indent=2).replace("\n", "\n  ") if not isinstance(body, str) else body[:500]))


def cancel(ticker: str, order_id: str, key_id: str, key, exchange_index: int | None = None):
    params = {"market_ticker": ticker}
    if exchange_index is not None:
        params["exchange_index"] = exchange_index
    return request("DELETE", f"/portfolio/events/orders/{urllib.parse.quote(order_id)}", key_id=key_id, key=key, params=params)


def cmd_balance() -> None:
    key_id, key = credentials()
    show("balance", *request("GET", "/portfolio/balance", key_id=key_id, key=key))


def cmd_order() -> None:
    key_id, key = credentials()
    m = pick_market()
    print(f"market {m['ticker']} (exchange_index {m.get('exchange_index')}), closes {m['close_time']}")
    cid = "demo-" + uuid.uuid4().hex[:12]
    st, d = request("POST", "/portfolio/events/orders", key_id=key_id, key=key,
                    body=order_body(m["ticker"], 1, 0.01, cid, m.get("exchange_index")))
    show("create order", st, d)
    if st == 200 and isinstance(d, dict) and d.get("order_id"):
        show("cancel order", *cancel(m["ticker"], d["order_id"], key_id, key, m.get("exchange_index")))


def classify_dup(order_ids: list[str]) -> str:
    """What the exchange did with two identical orders, from the order ids it accepted."""
    n, distinct = len(order_ids), len(set(order_ids))
    if n == 0:
        return "neither order was accepted, so nothing was learned. Read the responses above."
    if n == 1:
        return "ONE accepted and the second was REFUSED: the exchange rejects a repeated client_order_id."
    if distinct == 1:
        return "both calls returned the SAME order: a repeated client_order_id is idempotent."
    return "TWO different orders exist for one client_order_id: the exchange does NOT protect against duplicates."


def cmd_dup() -> None:
    """The same client_order_id twice. The docs do not say what happens; this finds out."""
    key_id, key = credentials()
    m = pick_market()
    cid = "dup-" + uuid.uuid4().hex[:12]
    body = order_body(m["ticker"], 1, 0.01, cid, m.get("exchange_index"))
    print(f"market {m['ticker']}, client_order_id {cid}, sending the identical order twice")
    ids = []
    for n in (1, 2):
        st, d = request("POST", "/portfolio/events/orders", key_id=key_id, key=key, body=body)
        show(f"attempt {n}", st, d)
        if isinstance(d, dict) and d.get("order_id"):
            ids.append(d["order_id"])
    distinct = sorted(set(ids))
    print("\nRESULT: " + classify_dup(ids))
    for oid in distinct:
        show(f"cancel {oid[:8]}", *cancel(m["ticker"], oid, key_id, key, m.get("exchange_index")))


def main() -> None:
    cmds = {"balance": cmd_balance, "order": cmd_order, "dup": cmd_dup}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit("usage: python3 -m scalper.demo balance | order | dup   (DEMO ONLY)")
    cmds[sys.argv[1]]()


if __name__ == "__main__":
    main()
