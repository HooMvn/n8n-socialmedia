from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = os.getenv("SMOKE_API_URL", "http://localhost:8000").rstrip("/")
WEB = os.getenv("SMOKE_WEB_URL", "http://localhost:3000").rstrip("/")


def get(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "risheh-engage-smoke/0.8"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def check(name: str, url: str, expected: int = 200) -> bool:
    status, body = get(url)
    ok = status == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {status} {url}")
    if not ok:
        print(body[:500])
    return ok


def main() -> int:
    checks = [
        check("api-health", f"{API}/health"),
        check("api-ready", f"{API}/ready"),
        check("api-metrics", f"{API}/metrics"),
        check("web-home", WEB),
        check("web-inbox", f"{WEB}/inbox"),
        check("web-ai-queue", f"{WEB}/ai-queue"),
        check("web-knowledge", f"{WEB}/knowledge"),
    ]
    status, body = get(f"{API}/health")
    if status == 200:
        try:
            payload = json.loads(body)
            print(f"environment={payload.get('environment')} service={payload.get('service')}")
        except json.JSONDecodeError:
            pass
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
