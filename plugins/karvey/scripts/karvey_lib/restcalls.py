"""REST forms of a release (REQ-HF-010..013, 015; architecture §1.3). Pure parsing, no network.

A command segment of an HTTP client (``curl``, ``wget``, HTTPie ``http``/``https``/``xh``, ``az rest``,
``gh api``, ``glab api``) becomes a :class:`Request` (method, URL without credentials or query, body); the
request is classified against the endpoint table into a :class:`Call`:

- ``pr-complete``: a pull/merge request completed (Azure Repos PATCH with ``status: completed`` or an
  auto-complete setter; GitHub ``PUT …/pulls/<n>/merge``; GitLab ``PUT …/merge_requests/<n>/merge``);
- ``ref-write``: a branch written through the API (GitHub ``git/refs``, ``merges``; Azure ``…/refs``);
- ``pipeline-approve``: a waiting run approved (Azure ``_apis/pipelines/approvals``; GitHub
  ``…/actions/runs/<id>/pending_deployments``);
- ``fail``: what cannot be verified (variables in the URL or body of such a request, an unreadable body,
  inline scripts that call these endpoints, approval forms that name no run).

Reads, non-completing updates and rejections give None (REQ-HF-013). Headers, ``-u`` credentials and
``user:pass@`` never reach a :class:`Call` (REQ-HF-015, 018).
"""
import json
import os
import re
from urllib.parse import unquote, urlsplit

BODY_MAX = 256 * 1024
CLIENTS = frozenset({"curl", "wget", "http", "https", "xh", "xhs"})
INLINE = {"python": ("-c",), "python3": ("-c",), "node": ("-e", "--eval", "-p"), "ruby": ("-e",),
          "perl": ("-e", "-E"), "pwsh": ("-c", "-Command", "-command"), "powershell": ("-c", "-Command", "-command"),
          "deno": ("eval",), "bun": ("-e", "--eval")}
METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})

# curl options that take a value (short letters and long names)
CURL_SHORT_ARG = set("XdHuoAebcFTKmwxErUtYyzCPQ")
CURL_LONG_ARG = {"--request", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode", "--json",
                 "--header", "--user", "--output", "--user-agent", "--referer", "--cookie", "--cookie-jar", "--form",
                 "--form-string", "--upload-file", "--config", "--max-time", "--write-out", "--proxy", "--cert",
                 "--key", "--cacert", "--resolve", "--connect-timeout", "--retry", "--retry-delay", "--url",
                 "--oauth2-bearer", "--proxy-user", "--interface", "--limit-rate", "--range", "--time-cond",
                 "--continue-at", "--quote", "--ciphers", "--capath", "--pass", "--netrc-file", "--aws-sigv4",
                 "--variable", "--expand-url", "--expand-data", "--expand-json", "--trace", "--trace-ascii",
                 "--stderr", "--dump-header", "--create-file-mode", "--happy-eyeballs-timeout-ms"}
CURL_DATA = {"-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode", "--json"}

_AZ_PR = re.compile(r"/_apis/git/repositories/([^/]+)/pullrequests/(\d+)/?$", re.I)
_AZ_REFS = re.compile(r"/_apis/git/repositories/([^/]+)/refs/?$", re.I)
_AZ_APPROVALS = re.compile(r"/_apis/pipelines/approvals(?:/([^/]+))?/?$", re.I)
_AZ_RELEASE = re.compile(r"/_apis/release/approvals", re.I)
_GH_MERGE = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/pulls/(\d+)/merge/?$")
_GH_REFS = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/git/refs(?:/heads)?/?(.*)$")
_GH_MERGES = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/merges/?$")
_GH_PENDING = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/actions/runs/(\d+)/pending_deployments/?$")
_GH_REVIEW = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/actions/runs/(\d+)/(approve|deployment_protection_rule)/?$")
_GL_MERGE = re.compile(r"/projects/([^/]+)/merge_requests/(\d+)/merge/?$")
_GL_DEPLOY = re.compile(r"/projects/([^/]+)/deployments/(\d+)/approval/?$")
# what an inline script or an unparsed body may call (REQ-HF-015)
_ENDPOINT_TEXT = re.compile(r"pullrequests/\d+|pulls/\d+/merge|merge_requests/\d+/merge|pipelines/approvals|"
                            r"pending_deployments|release/approvals|git/refs|/merges\b|deployments/\d+/approval",
                            re.I)
_COMPLETING_TEXT = re.compile(r"""["']?status["']?\s*[:=]\s*["']?(completed|approved)|autoCompleteSetBy|"""
                              r"""["']?state["']?\s*[:=]\s*["']?approved""", re.I)


class Request:
    __slots__ = ("client", "method", "url", "body", "body_text", "unreadable", "variable")

    def __init__(self, client):
        self.client, self.method, self.url = client, None, None
        self.body, self.body_text, self.unreadable, self.variable = None, None, None, False


class Call:
    """A classified request. ``kind``: pr-complete · ref-write · pipeline-approve · fail."""

    __slots__ = ("kind", "host", "repo", "number", "org", "project", "bound", "deferred", "branch", "approvals",
                 "run", "reason", "url", "client")

    def __init__(self, kind, **kw):
        self.kind = kind
        for k in self.__slots__[1:]:
            setattr(self, k, kw.get(k))

    def __repr__(self):
        return "Call(%s)" % ", ".join("%s=%r" % (k, getattr(self, k)) for k in self.__slots__)


def _has_var(text):
    return isinstance(text, str) and ("$" in text or "`" in text)


def clean_url(raw):
    """The URL without credentials, query or fragment (``https://host/path``); None when not http(s)."""
    if not isinstance(raw, str) or not raw:
        return None
    u = raw if re.match(r"^[a-z]+://", raw, re.I) else None
    if u is None:
        return None
    try:
        parts = urlsplit(u)
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https"):
        return None
    host = parts.hostname or ""
    if parts.port:
        host += ":%d" % parts.port
    return "%s://%s%s" % (parts.scheme.lower(), host.lower(), parts.path)


def _read_body(arg, cwd):
    """``(text, unreadable_reason)`` of a body argument (``@file`` read from ``cwd``, max 256 KB)."""
    if not arg.startswith("@"):
        return arg, None
    path = arg[1:]
    if path in ("-", ""):
        return None, "the body comes from stdin"
    if _has_var(path):
        return None, "the body file is built from variables"
    full = path if os.path.isabs(path) else os.path.join(cwd or os.getcwd(), path)
    try:
        if not os.path.isfile(full) or os.path.getsize(full) > BODY_MAX:
            return None, "the body file %s cannot be read" % path
        with open(full, encoding="utf-8", errors="replace") as fh:
            return fh.read(), None
    except OSError:
        return None, "the body file %s cannot be read" % path


def _parse_curl(seg):
    r = Request("curl")
    a = seg.argv[1:]
    data, urls, i, get = [], [], 0, False
    upload = False
    while i < len(a):
        x = a[i]
        if x == "--":
            urls += a[i + 1:]
            break
        if x.startswith("--"):
            name, eq, val = x.partition("=")
            if name in CURL_LONG_ARG:
                if not eq:
                    i += 1
                    val = a[i] if i < len(a) else ""
                if name == "--request":
                    r.method = val.upper()
                elif name in CURL_DATA:
                    data.append(val)
                elif name == "--url":
                    urls.append(val)
                elif name == "--upload-file":
                    upload = True
                elif name == "--config":
                    r.unreadable = "curl --config hides the request"
            elif name == "--get":
                get = True
            i += 1
            continue
        if x.startswith("-") and len(x) > 1:
            j = 1
            while j < len(x):
                ch = x[j]
                if ch in CURL_SHORT_ARG:
                    val = x[j + 1:]
                    if not val:
                        i += 1
                        val = a[i] if i < len(a) else ""
                    if ch == "X":
                        r.method = val.upper()
                    elif ch == "d":
                        data.append(val)
                    elif ch == "T":
                        upload = True
                    elif ch == "K":
                        r.unreadable = "curl --config hides the request"
                    break
                if ch == "G":
                    get = True
                j += 1
            i += 1
            continue
        urls.append(x)
        i += 1
    r.url = urls[0] if urls else None
    texts = []
    for d in data:
        t, why = _read_body(d, seg.cwd)
        if why:
            r.unreadable = r.unreadable or why
        elif t is not None:
            texts.append(t)
    r.body_text = "&".join(texts) if texts else None
    r.variable = _has_var(r.url) or any(_has_var(d) for d in data)
    if r.method is None:
        r.method = "GET" if get else ("PUT" if upload else ("POST" if data else "GET"))
    return r


def _parse_wget(seg):
    r = Request("wget")
    body = []
    for x in seg.argv[1:]:
        if x.startswith("--method="):
            r.method = x.split("=", 1)[1].upper()
        elif x.startswith(("--body-data=", "--post-data=")):
            body.append(x.split("=", 1)[1])
            r.method = r.method or "POST"
        elif x.startswith(("--body-file=", "--post-file=")):
            t, why = _read_body("@" + x.split("=", 1)[1], seg.cwd)
            r.unreadable = r.unreadable or why
            if t is not None:
                body.append(t)
            r.method = r.method or "POST"
        elif not x.startswith("-") and r.url is None:
            r.url = x
    r.method = r.method or "GET"
    r.body_text = "&".join(body) if body else None
    r.variable = _has_var(r.url) or any(_has_var(b) for b in body)
    return r


def _parse_httpie(seg):
    r = Request("httpie")
    pos = [x for x in seg.argv[1:] if not x.startswith("-")]
    if pos and pos[0].upper() in METHODS:
        r.method = pos.pop(0).upper()
    if pos:
        r.url = pos.pop(0)
        if not re.match(r"^[a-z]+://", r.url, re.I):
            r.url = ("https://" if seg.argv0 in ("https", "xhs") else "http://") + r.url
    body = {}
    for item in pos:
        m = re.match(r"^([^:=@]+)(:=|=|==|:|@)(.*)$", item, re.S)
        if not m or m.group(2) in (":", "=="):
            continue
        k, op, v = m.groups()
        if op == ":=":
            try:
                body[k] = json.loads(v)
            except ValueError:
                body[k] = v
        else:
            body[k] = v
        if _has_var(item):
            r.variable = True
    if body:
        r.body = body
    r.method = r.method or ("POST" if body else "GET")
    r.variable = r.variable or _has_var(r.url)
    return r


def _fields(a, names):
    out = {}
    for i, x in enumerate(a):
        for n in names:
            val = None
            if x == n and i + 1 < len(a):
                val = a[i + 1]
            elif x.startswith(n + "="):
                val = x[len(n) + 1:]
            if val is not None and "=" in val:
                k, _, v = val.partition("=")
                out[k] = v
    return out


def _parse_cli_api(seg, tool):
    """``az rest`` / ``gh api`` / ``glab api``."""
    r = Request(tool)
    a = seg.argv[1:]
    from_opt = lambda *names: next((a[i + 1] if x in names and i + 1 < len(a) else x.split("=", 1)[1]  # noqa: E731
                                    for i, x in enumerate(a) if x in names or any(x.startswith(n + "=")
                                                                                   for n in names)), None)
    if tool == "az":
        r.method = (from_opt("--method", "-m") or "GET").upper()
        r.url = from_opt("--url", "--uri", "-u")
        b = from_opt("--body", "-b")
        if b is not None:
            t, why = _read_body(b, seg.cwd)
            r.unreadable, r.body_text = why, t
        r.variable = _has_var(r.url) or _has_var(b)
        return r
    rest = a[1:]  # after "api"
    fields = _fields(rest, ("-f", "-F", "--field", "--raw-field"))
    m = from_opt("-X", "--method")
    pos = [x for i, x in enumerate(rest) if not x.startswith("-") and
           (i == 0 or rest[i - 1] not in ("-X", "--method", "-f", "-F", "--field", "--raw-field", "-H", "--header",
                                          "--input", "-q", "--jq", "-t", "--template", "--hostname", "-p",
                                          "--preview", "--cache"))]
    r.url = pos[0] if pos else None
    inp = from_opt("--input")
    if inp is not None:
        t, why = _read_body("@" + inp if not inp.startswith("@") else inp, seg.cwd)
        r.unreadable, r.body_text = why, t
    if fields:
        r.body = fields
    r.method = (m or ("POST" if fields or inp else "GET")).upper()
    r.variable = _has_var(r.url) or any(_has_var(v) for v in fields.values())
    if r.url and not re.match(r"^[a-z]+://", r.url, re.I):
        host = "api.github.com" if tool == "gh" else "gitlab.invalid/api/v4"
        r.url = "https://%s/%s" % (host, r.url.lstrip("/"))
    return r


def parse_request(seg):
    """The :class:`Request` of an HTTP-client segment, or None."""
    name = seg.argv0
    a = seg.argv[1:]
    if name == "curl":
        return _parse_curl(seg)
    if name == "wget":
        return _parse_wget(seg)
    if name in ("http", "https", "xh", "xhs"):
        return _parse_httpie(seg)
    if name == "az" and a[:1] == ["rest"]:
        return _parse_cli_api(seg, "az")
    if name in ("gh", "glab") and a[:1] == ["api"]:
        return _parse_cli_api(seg, name)
    return None


def _body_obj(r):
    if r.body is not None:
        return r.body
    t = r.body_text
    if not t:
        return None
    try:
        return json.loads(t)
    except ValueError:
        pass
    out = {}
    for part in t.split("&"):
        k, sep, v = part.partition("=")
        if sep:
            out[unquote(k)] = unquote(v)
    return out or t


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _eq(v, word):
    return isinstance(v, str) and v.strip().lower() == word


def _azure_org(url):
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    segs = [s for s in p.path.split("/") if s]
    if host in ("dev.azure.com", "vsrm.dev.azure.com") and segs:
        return "https://dev.azure.com/%s" % segs[0], (segs[1] if len(segs) > 1 and segs[1] != "_apis" else None)
    if host.endswith(".visualstudio.com"):
        return "https://%s" % host, (segs[0] if segs and segs[0] != "_apis" else None)
    return None, None


def classify(r):
    """The :class:`Call` a request makes, or None (a read, a non-completing update, a rejection, another API)."""
    raw = r.url or ""
    url = clean_url(raw) if not _has_var(raw) else None
    method = (r.method or "GET").upper()
    if url is None:
        if _has_var(raw) and (_ENDPOINT_TEXT.search(raw) or _COMPLETING_TEXT.search(r.body_text or "") or
                              _COMPLETING_TEXT.search(json.dumps(r.body) if r.body else "")):
            return Call("fail", reason="the request URL is built from variables; write the URL out in full",
                        client=r.client)
        return None
    path = urlsplit(url).path
    writes = method not in ("GET", "HEAD", "OPTIONS")
    if not writes:
        return None
    if _has_var(raw):  # pragma: no cover - handled above
        return None
    endpoint = _ENDPOINT_TEXT.search(path)
    if endpoint and (r.unreadable or r.variable):
        return Call("fail", url=url, client=r.client,
                    reason="cannot verify the request to %s: %s" % (url, r.unreadable or
                                                                     "its body is built from variables"))
    body = _body_obj(r)
    dicts = list(_walk(body)) if body is not None else []
    # Azure Repos: complete or set auto-complete on a PR
    m = _AZ_PR.search(path)
    if m and method == "PATCH":
        completed = any(_eq(d.get("status"), "completed") for d in dicts)
        auto = any("autoCompleteSetBy" in d for d in dicts)
        if not (completed or auto):
            return None
        bound = None
        for d in dicts:
            lm = d.get("lastMergeSourceCommit")
            if isinstance(lm, dict) and isinstance(lm.get("commitId"), str):
                bound = lm["commitId"].lower()
        org, project = _azure_org(url)
        return Call("pr-complete", host="azure", repo=unquote(m.group(1)), number=m.group(2), org=org,
                    project=project, bound=bound, deferred=not completed, url=url, client=r.client)
    m = _GH_MERGE.search(path)
    if m and method in ("PUT", "POST"):
        sha = next((d.get("sha") for d in dicts if isinstance(d.get("sha"), str)), None)
        return Call("pr-complete", host="github", repo=m.group(1), number=m.group(2),
                    bound=sha.lower() if sha else None, deferred=False, url=url, client=r.client)
    m = _GL_MERGE.search(path)
    if m and method in ("PUT", "POST"):
        proj = unquote(m.group(1))
        if proj.isdigit():
            return Call("fail", url=url, client=r.client,
                        reason="a GitLab project id (%s) cannot be tied to a local clone; run glab mr merge from "
                               "the clone" % proj)
        sha = next((d.get("sha") for d in dicts if isinstance(d.get("sha"), str)), None)
        auto = any(str(d.get("merge_when_pipeline_succeeds", "")).lower() == "true" or
                   str(d.get("auto_merge", "")).lower() == "true" for d in dicts)
        return Call("pr-complete", host="gitlab", repo=proj, number=m.group(2), bound=sha.lower() if sha else None,
                    deferred=auto, url=url, client=r.client)
    m = _GH_REFS.search(path)
    if m:
        branch = m.group(2).strip("/") or None
        if branch is None:
            branch = next((d.get("ref") for d in dicts if isinstance(d.get("ref"), str)), None)
        if branch and branch.startswith("refs/heads/"):
            branch = branch[len("refs/heads/"):]
        if branch and branch.startswith(("refs/tags/", "tags/")):
            return None
        return Call("ref-write", host="github", repo=m.group(1), branch=branch, url=url, client=r.client)
    m = _GH_MERGES.search(path)
    if m:
        base = next((d.get("base") for d in dicts if isinstance(d.get("base"), str)), None)
        return Call("ref-write", host="github", repo=m.group(1), branch=base, url=url, client=r.client)
    m = _AZ_REFS.search(path)
    if m and method == "POST":
        names = [d.get("name") for d in dicts if isinstance(d.get("name"), str)]
        heads = [n[len("refs/heads/"):] for n in names if n.startswith("refs/heads/")]
        if not names:
            return Call("ref-write", host="azure", repo=unquote(m.group(1)), branch=None, url=url, client=r.client)
        if not heads:
            return None
        return Call("ref-write", host="azure", repo=unquote(m.group(1)), branch=heads[0] if len(heads) == 1 else None,
                    url=url, client=r.client)
    m = _AZ_APPROVALS.search(path)
    if m and method in ("PATCH", "POST"):
        ids = [str(d.get("approvalId")) for d in dicts if _eq(d.get("status"), "approved") and d.get("approvalId")]
        if not ids:
            if any(_eq(d.get("status"), "approved") for d in dicts):
                return Call("fail", url=url, client=r.client, reason="a pipeline approval that names no approvalId")
            return None
        org, project = _azure_org(url)
        return Call("pipeline-approve", host="azure", approvals=ids, org=org, project=project, url=url,
                    client=r.client)
    m = _GH_PENDING.search(path)
    if m and method == "POST":
        if not any(_eq(d.get("state"), "approved") for d in dicts):
            return None
        return Call("pipeline-approve", host="github", repo=m.group(1), run=m.group(2), url=url, client=r.client)
    if _GH_REVIEW.search(path) or _AZ_RELEASE.search(path) or _GL_DEPLOY.search(path):
        if _GL_DEPLOY.search(path) and not any(_eq(d.get("status"), "approved") for d in dicts):
            return None
        if _AZ_RELEASE.search(path) and not any(_eq(d.get("status"), "approved") for d in dicts):
            return None
        return Call("fail", url=url, client=r.client,
                    reason="this approval form names no run the gate can resolve (%s); approve it in the host's "
                           "UI after the production OK" % path)
    return None


def inline_call(seg):
    """A ``fail`` :class:`Call` for an inline script that calls a completion or approval endpoint."""
    opts = INLINE.get(seg.argv0)
    if not opts:
        return None
    a = seg.argv[1:]
    for i, x in enumerate(a):
        if x in opts and i + 1 < len(a):
            script = a[i + 1]
            if _ENDPOINT_TEXT.search(script) or re.search(r"Invoke-(RestMethod|WebRequest)", script, re.I) and \
                    _COMPLETING_TEXT.search(script):
                return Call("fail", client=seg.argv0,
                            reason="an inline %s script calls a PR completion or approval endpoint, which the gate "
                                   "cannot read; send the request with curl, gh, az or glab instead" % seg.argv0)
    return None


def classify_segment(seg):
    """The :class:`Call` of one segment (HTTP client or inline script), or None."""
    if not seg.argv:
        return None
    c = inline_call(seg)
    if c is not None:
        return c
    r = parse_request(seg)
    if r is None:
        return None
    return classify(r)


def target_of(call):
    """The repo name a call targets (``owner/name`` or ``name``), or None."""
    return call.repo if call is not None else None
