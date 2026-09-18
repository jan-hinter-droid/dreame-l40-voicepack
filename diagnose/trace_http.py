#!/usr/bin/env python3
"""
HTTP-Tracing, korrekt an der Session NACH dem Login.

Die Bridge ersetzt ihre requests-Session beim Login - ein Spion, der vorher
gesetzt wird, sieht nichts. Hier wird nach login() erneut angehaengt.
Nur lesende Aufrufe.
"""
from __future__ import annotations

import importlib.util
import json
import sys

BRIDGE = "/home/pi/dreame_fhem_bridge.py"

spec = importlib.util.spec_from_file_location("dreame_bridge_probe", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
sys.modules["dreame_bridge_probe"] = bridge
spec.loader.exec_module(bridge)

token = bridge.load_token()
cloud = bridge.CloudClass(
    username=bridge.USERNAME,
    password="",
    account_type=bridge.ACCOUNT_TYPE,
    country=bridge.COUNTRY,
    auth_key=token,
    did=bridge.DEVICE_ID,
)

print("[i] Login ...")
if not cloud.login():
    sys.exit("Login fehlgeschlagen")
print("[i] Login OK")

trace: list[dict] = []


def attach(session) -> None:
    original_post = session.post

    def spying_post(url, *args, **kwargs):
        response = original_post(url, *args, **kwargs)
        body = kwargs.get("data") or (args[0] if args else None)
        trace.append({
            "url": str(url),
            "status": response.status_code,
            "body": (body or "")[:300] if isinstance(body, str) else str(body)[:300],
            "text": response.text[:300],
        })
        return response

    session.post = spying_post
    return session


attach(cloud._session)


def show(label: str, start: int) -> None:
    print("\n" + "=" * 74)
    print(label)
    print("=" * 74)
    for entry in trace[start:]:
        print(f"  HTTP {entry['status']}  {entry['url']}")
        print(f"    BODY   : {entry['body']}")
        print(f"    ANTWORT: {entry['text']}")
    if not trace[start:]:
        print("  (kein HTTP-Aufruf - laeuft NICHT ueber REST)")


n = len(trace)
info = cloud.get_device_info()
show("get_device_info()", n)
if info:
    print(f"  -> Modell: {info.get('model')}  Host: {cloud._host}")

n = len(trace)
result = cloud.send("get_properties", [
    {"did": str(bridge.DEVICE_ID), "siid": 7, "piid": 2},
    {"did": str(bridge.DEVICE_ID), "siid": 7, "piid": 3},
], retry_count=1, timeout=20)
show("cloud.send('get_properties', siid7 piid2/3)", n)
print("\n  Rueckgabewert:", json.dumps(result, ensure_ascii=False)[:500])

print("\n[i] Fertig.")
