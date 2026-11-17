#!/usr/bin/env python3
"""SUUMO detail fetch + parse. --parse-only reads cache only. --limit-sample N fetches first N of each type."""
import csv, hashlib, json, os, re, subprocess, sys, time, datetime, unicodedata, fnmatch
from urllib.parse import urlparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = f"{BASE}/wave3/targets-suumo.csv"
ROBOTS = f"{BASE}/wave1/robots/suumo.jp.txt"
CACHE = "/tmp/claude-0/-home-user-bd-chunk-project/8a1dfd2a-b2c8-5e83-818a-2a83491f1fc3/scratchpad/wave3/raw-suumo"
LOG = f"{BASE}/wave3/requests-suumo.log"
OUT = f"{BASE}/wave3/data/details-suumo.csv"
SUMMARY = f"{BASE}/wave3/details-suumo-summary.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
BUDGET = 520
os.makedirs(CACHE, exist_ok=True)

def robots_rules():
    rules, grp = [], False
    for l in open(ROBOTS, encoding='utf-8'):
        l = l.split('#')[0].strip()
        if l.lower().startswith('user-agent:'):
            grp = l.split(':', 1)[1].strip() == '*'
        elif grp and l.lower().startswith('disallow:'):
            p = l.split(':', 1)[1].strip()
            if p: rules.append(p)
    return rules
RULES = robots_rules()
def allowed(url):
    u = urlparse(url); path = u.path + ('?' + u.query if u.query else '')
    for r in RULES:
        pat = re.escape(r).replace(r'\*', '.*')
        if r.endswith('$'): pat = re.escape(r[:-1]).replace(r'\*', '.*') + '$'
        if re.match(pat, path): return False
    return True

def key(url): return hashlib.sha1(url.encode()).hexdigest()
def cpath(url): return f"{CACHE}/{key(url)}.html"
def cached(url): return os.path.exists(cpath(url)) and os.path.exists(cpath(url)[:-5] + '.meta')
def load(url):
    if not cached(url): return None, None
    meta = json.load(open(cpath(url)[:-5] + '.meta'))
    return meta, open(cpath(url), encoding='utf-8', errors='replace').read()

class Stop(Exception): pass
state = {'requests': 0, 'last': 0.0}
def count_logged():
    return sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0

def fetch(url):
    if cached(url): return load(url)
    if not allowed(url): raise Stop(f"robots disallow {url}")
    if count_logged() >= BUDGET: raise Stop("budget")
    wait = 3.4 - (time.time() - state['last'])
    if wait > 0: time.sleep(wait)
    r = subprocess.run(['curl', '-sS', '-L', '--compressed', '-A', UA, '-H', 'Accept-Language: ja',
                        '--max-time', '40', '-w', '\n%{http_code}', url], capture_output=True)
    state['last'] = time.time()
    state['requests'] += 1
    out = r.stdout
    body, _, code = out.rpartition(b'\n')
    code = code.decode().strip() or '000'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(LOG, 'a') as f: f.write(f"{now}\t{code}\t{url}\n")
    if code in ('401', '403', '429'): raise Stop(f"HTTP {code} {url}")
    if code == '000' or r.returncode != 0:
        raise Stop(f"curl error rc={r.returncode} {r.stderr.decode()[:200]} {url}")
    txt = body.decode('utf-8', errors='replace')
    if not txt.strip(): raise Stop(f"empty body {url}")
    if re.search(r'captcha|recaptcha|アクセスが集中|Access Denied|robot check', txt[:6000], re.I) and len(txt) < 20000:
        raise Stop(f"challenge page {url}")
    open(cpath(url), 'w', encoding='utf-8').write(txt)
    meta = {'url': url, 'fetched_at': now, 'http_status': int(code)}
    json.dump(meta, open(cpath(url)[:-5] + '.meta', 'w'))
    return meta, txt
