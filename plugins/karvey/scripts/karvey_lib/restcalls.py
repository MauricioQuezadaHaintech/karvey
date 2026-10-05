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
                 "--request-target", "--connect-to", "--expand-header", "--expand-user",
                 "--stderr", "--dump-header", "--create-file-mode", "--happy-eyeballs-timeout-ms"}
CURL_DATA = {"-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode", "--json"}

_AZ_PR = re.compile(r"/_apis/git/repositories/([^/]+)/pullrequests/(\d+)/?$", re.I)
_AZ_PUSHES = re.compile(r"/_apis/git/repositories/([^/]+)/pushes/?$", re.I)
_GH_CONTENTS = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/contents(?:/.*)?$", re.I)
_GL_REPO_WRITE = re.compile(r"/projects/(.+?)/repository/(files/.+|commits)/?$", re.I)
_GRAPHQL = re.compile(r"/graphql/?$", re.I)
_AZ_REFS = re.compile(r"/_apis/git/repositories/([^/]+)/refs/?$", re.I)
_AZ_APPROVALS = re.compile(r"/_apis/pipelines/approvals(?:/([^/]+))?/?$", re.I)
_AZ_RELEASE = re.compile(r"/_apis/release/approvals", re.I)
_GH_MERGE = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/pulls/(\d+)/merge/?$", re.I)
_GH_REFS = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/git/refs(?:/heads)?/?(.*)$", re.I)
_GH_MERGES = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/merges/?$", re.I)
_GH_PENDING = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/actions/runs/(\d+)/pending_deployments/?$", re.I)
_GH_REVIEW = re.compile(r"(?:^|/)repos/([^/]+/[^/]+)/actions/runs/(\d+)/(approve|deployment_protection_rule)/?$", re.I)
_GL_MERGE = re.compile(r"/projects/(.+?)/merge_requests/(\d+)/merge/?$", re.I)
_GL_DEPLOY = re.compile(r"/projects/(.+?)/deployments/(\d+)/approval/?$", re.I)
# what an inline script or an unparsed body may call (REQ-HF-015)
_SEG = r"[^/\s\"'?]+"
_ENDPOINT_TEXT = re.compile(r"pullrequests/%(s)s|pulls/%(s)s/merge|merge_requests/%(s)s/merge|pipelines/approvals|"
                            r"pending_deployments|release/approvals|repos/%(s)s/%(s)s/git/refs|repos/%(s)s/%(s)s/merges|"
                            r"repos/%(s)s/%(s)s/contents/|_apis/git/repositories/%(s)s/(refs|pushes)|"
                            r"deployments/%(s)s/approval|/graphql\b|repository/(files|commits)" % {"s": _SEG}, re.I)
_GRAPHQL_WRITE = re.compile(r"\b(mergePullRequest|enablePullRequestAutoMerge|updateRef|updateRefs|"
                            r"createCommitOnBranch|deleteRef|mergeBranch|updatePullRequestBranch)\b")
_WRITE_VERB = re.compile(r"\b(patch|put|post|delete)\b|-X\s*(PATCH|PUT|POST|DELETE)|method\s*[:=]", re.I)
_URL_TOKEN = re.compile(r"https?://\S+", re.I)
# a code host's API (BUG-152): a request to one that the parser cannot read fails closed
_CODE_HOST = re.compile(r"^https?://([^/]*\b(github|gitlab|azure|visualstudio)\b[^/]*|[^/]+/(api/v[34]|_apis)\b)",
                        re.I)
_COMPLETING_TEXT = re.compile(r"""["']?status["']?\s*[:=]\s*["']?(completed|approved)|autoCompleteSetBy|"""
                              r"""["']?state["']?\s*[:=]\s*["']?approved""", re.I)


class Request:
    __slots__ = ("client", "method", "url", "urls", "body", "body_text", "unreadable", "variable")

    def __init__(self, client):
        self.client, self.method, self.url, self.urls = client, None, None, []
        self.body, self.body_text, self.unreadable, self.variable = None, None, None, False


CRED_OPTS = {"-u", "--user", "-H", "--header", "-a", "--auth", "--oauth2-bearer", "--proxy-user", "-E", "--cert",
             "--key", "--pass", "-b", "--cookie", "-A", "--user-agent", "-e", "--referer", "--password",
             "--http-user", "--http-password", "--session", "-o", "--output", "-O", "--output-document"}


def _scheme_urls(args):
    """BUG-146: every argument that is an http(s) URL is a request target, whatever option precedes it; a
    variable counts as a possible URL unless it is the value of a credential, header or output option."""
    out = []
    for i, a in enumerate(args):
        if not isinstance(a, str):
            continue
        if re.match(r"^https?://", a, re.I):
            out.append(a)
        elif re.match(r"^[\"']?(\$|`)", a) and not (i > 0 and args[i - 1] in CRED_OPTS):
            out.append(a)
    return out


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
    try:
        if parts.port:
            host += ":%d" % parts.port
    except ValueError:
        return None
    path = parts.path
    for _ in range(3):  # BUG-146: %70ulls/… is pulls/… on the host
        dec = unquote(path)
        if dec == path:
            break
        path = dec
    return "%s://%s%s" % (parts.scheme.lower(), host.lower(), remove_dot_segments(re.sub(r"/{2,}", "/", path)))


def remove_dot_segments(path):
    """RFC 3986 §5.2.4, as curl and the hosts apply it (BUG-151: ``…/12/./merge``)."""
    out = []
    for seg in path.split("/"):
        if seg == ".":
            continue
        if seg == "..":
            if len(out) > 1:
                out.pop()
            continue
        out.append(seg)
    res = "/".join(out)
    if path.endswith(("/.", "/..")):
        res += "/"
    return res


GLOB_MAX = 32


def expand_curl_glob(url):
    """The URLs curl's globbing makes of ``url`` (``{a,b}`` and ``[1-3]``/``[a-c]``), or None when there are more
    than ``GLOB_MAX`` or the pattern cannot be read (BUG-151)."""
    out = [url]
    pat = re.compile(r"\{([^{}]*)\}|\[([0-9]+|[a-zA-Z])-([0-9]+|[a-zA-Z])(?::[0-9]+)?\]")
    for _ in range(8):
        nxt, changed = [], False
        for u in out:
            m = pat.search(u)
            if not m:
                nxt.append(u)
                continue
            changed = True
            if m.group(1) is not None:
                alts = m.group(1).split(",")
            else:
                a, b = m.group(2), m.group(3)
                if a.isdigit() and b.isdigit():
                    lo, hi = int(a), int(b)
                    if hi < lo or hi - lo > GLOB_MAX:
                        return None
                    alts = [str(n).zfill(len(a)) for n in range(lo, hi + 1)]
                elif a.isalpha() and b.isalpha() and ord(b) >= ord(a) and ord(b) - ord(a) <= GLOB_MAX:
                    alts = [chr(c) for c in range(ord(a), ord(b) + 1)]
                else:
                    return None
            nxt += [u[:m.start()] + alt + u[m.end():] for alt in alts]
            if len(nxt) > GLOB_MAX:
                return None
        out = nxt
        if not changed:
            return out
    return None


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
    """curl: every URL argument (BUG-146: unknown options, -D, several URLs, --next), the last explicit method,
    the bodies; ``-K``/``--config`` hides the request."""
    r = Request("curl")
    a = seg.argv[1:]
    data, explicit, i, get, upload, target = [], [], 0, False, False, None
    while i < len(a):
        x = a[i]
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
                    explicit.append(val)
                elif name == "--upload-file":
                    upload = True
                elif name == "--config":
                    r.unreadable = "curl --config hides the request"
                elif name == "--request-target":  # BUG-152: the path sent is this one, not the URL's
                    target = val
                elif name == "--variable" or name.startswith("--expand-"):  # BUG-152: {{var}} expansion
                    r.unreadable = r.unreadable or "curl %s builds the request from variables" % name
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
        i += 1
    urls = list(dict.fromkeys(explicit + _scheme_urls(a)))
    globoff = any(x in ("-g", "--globoff") or (re.match(r"^-[a-zA-Z]+$", x) and "g" in x[1:] and
                                                 not any(ch in CURL_SHORT_ARG for ch in x[1:x.index("g")]))
                  for x in a)
    r.urls = []
    for u in urls:
        if not globoff and re.search(r"[{}\[\]]", u):
            exp = expand_curl_glob(u)
            if exp is None:
                r.unreadable = r.unreadable or "the URL glob %s cannot be expanded; use -g or write it out" % u
                continue
            r.urls += exp
        else:
            r.urls.append(u)
    if target is not None:
        if _has_var(target) or not target.startswith("/"):
            r.unreadable = r.unreadable or "--request-target %s cannot be verified" % target
        else:
            r.urls = [re.sub(r"^(https?://[^/]+).*$", r"\1", u, flags=re.I) + target for u in r.urls
                      if re.match(r"^https?://", u, re.I)] or r.urls
    if "--path-as-is" in a and any(re.search(r"/\.\.?(/|$|\?)", u) for u in r.urls):
        r.unreadable = r.unreadable or "--path-as-is with dot segments in the URL"
    r.url = r.urls[0] if r.urls else None
    texts = []
    for d in data:
        t, why = _read_body(d, seg.cwd)
        if why:
            r.unreadable = r.unreadable or why
        elif t is not None:
            texts.append(t)
    r.body_text = "&".join(texts) if texts else None
    r.variable = any(_has_var(u) for u in r.urls) or any(_has_var(d) for d in data)
    if r.method is None:
        r.method = "GET" if get else ("PUT" if upload else ("POST" if data else "GET"))
    return r


WGET_WITH_ARG = {"--method", "--body-data", "--body-file", "--post-data", "--post-file", "--header", "-O",
                 "--output-document", "-o", "--output-file", "-a", "--append-output", "-e", "--execute", "-U",
                 "--user-agent", "--user", "--password", "-P", "--directory-prefix", "-i", "--input-file", "-t",
                 "--tries", "-T", "--timeout", "--load-cookies", "--save-cookies", "--referer"}


def _parse_wget(seg):
    r = Request("wget")
    a = seg.argv[1:]
    body, i = [], 0
    while i < len(a):
        x = a[i]
        name, eq, val = x.partition("=")
        if name in WGET_WITH_ARG:
            if not eq:
                i += 1
                val = a[i] if i < len(a) else ""
            if name == "--method":
                r.method = val.upper()
            elif name in ("--body-data", "--post-data"):
                body.append(val)
                r.method = r.method or "POST"
            elif name in ("--body-file", "--post-file"):
                t, why = _read_body("@" + val, seg.cwd)
                r.unreadable = r.unreadable or why
                if t is not None:
                    body.append(t)
                r.method = r.method or "POST"
            elif name in ("-i", "--input-file", "-e", "--execute"):
                r.unreadable = "wget %s hides the request" % name
        i += 1
    r.urls = _scheme_urls(a)
    r.url = r.urls[0] if r.urls else None
    r.method = r.method or "GET"
    r.body_text = "&".join(body) if body else None
    r.variable = any(_has_var(u) for u in r.urls) or any(_has_var(b) for b in body)
    return r


HTTPIE_WITH_ARG = {"-a", "--auth", "-A", "--auth-type", "--session", "--session-read-only", "-o", "--output",
                   "--verify", "--cert", "--cert-key", "--proxy", "--timeout", "--max-redirects", "--style", "-s",
                   "--print", "-p", "--pretty", "--format-options", "--response-charset", "--response-mime",
                   "--boundary", "--raw", "-m", "--method"}


def _parse_httpie(seg):
    """HTTPie / xh / httpx-style: ``[METHOD] URL [items]``; option values (``-a user:token``) are never the URL."""
    r = Request("httpie")
    a = seg.argv[1:]
    pos, i = [], 0
    while i < len(a):
        x = a[i]
        name, eq, val = x.partition("=")
        if x.startswith("-"):
            if name in HTTPIE_WITH_ARG and not eq:
                if name in ("-m", "--method") and i + 1 < len(a):
                    r.method = a[i + 1].upper()
                i += 2
                continue
            if name in ("-m", "--method") and eq:
                r.method = val.upper()
            i += 1
            continue
        pos.append(x)
        i += 1
    if pos and pos[0].upper() in METHODS:
        r.method = pos.pop(0).upper()
    if pos:
        u = pos.pop(0)
        if not re.match(r"^[a-z]+://", u, re.I) and not _has_var(u):
            u = ("https://" if seg.argv0 in ("https", "xhs") else "http://") + u
        r.urls = [u]
    r.urls += [u for u in _scheme_urls(pos) if u not in r.urls]
    r.url = r.urls[0] if r.urls else None
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
    r.variable = r.variable or any(_has_var(u) for u in r.urls)
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
        r.urls = [r.url] if r.url else []
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
    if r.url and not re.match(r"^[a-z]+://", r.url, re.I) and not _has_var(r.url.split("/", 1)[0]):
        host = "api.github.com" if tool == "gh" else "gitlab.invalid/api/v4"
        r.url = "https://%s/%s" % (host, r.url.lstrip("/"))
    r.urls = [r.url] if r.url else []
    return r


def parse_request(seg):
    """The :class:`Request` of an HTTP-client segment, or None."""
    name = posix_base(seg.argv0)
    a = seg.argv[1:]
    if name == "curl":
        return _parse_curl(seg)
    if name == "wget":
        return _parse_wget(seg)
    if name in ("http", "https", "xh", "xhs", "httpx", "curlie"):
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
    return (isinstance(v, str) and v.strip().lower() == word) or (isinstance(v, (int, str)) and _num_status(v, word))


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
    """The :class:`Call` a request makes (the first ``fail``, else the first candidate over every URL), or None."""
    if r.unreadable and (not r.urls or any(_CODE_HOST.search(u or "") for u in r.urls)):
        return Call("fail", client=r.client, reason="cannot verify the request: %s" % r.unreadable)
    found = None
    for u in (r.urls or [None]):
        c = _classify_one(r, u)
        if c is not None and c.kind == "fail":
            return c
        found = found or c
    return found


def _num_status(v, word):
    """Azure enums may come as numbers: PR status completed = 3, approval status approved = 4."""
    return (word == "completed" and str(v) == "3") or (word == "approved" and str(v) == "4")


def _classify_one(r, raw):
    raw = raw or ""
    url = clean_url(raw) if not _has_var(raw) else None
    method = (r.method or "GET").upper()
    if url is None:
        if _has_var(raw) and (_ENDPOINT_TEXT.search(raw) or _COMPLETING_TEXT.search(r.body_text or "") or
                              _GRAPHQL_WRITE.search(r.body_text or "") or
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
    if _GRAPHQL.search(path):  # BUG-146: a GraphQL mutation that merges or writes a branch
        text = (r.body_text or "") + (json.dumps(r.body) if r.body else "")
        if _GRAPHQL_WRITE.search(text):
            return Call("fail", url=url, client=r.client, reason="a GraphQL mutation that merges or writes a branch "
                                                                 "cannot be verified; merge through the PR command")
        return None
    m = _GH_CONTENTS.search(path)
    if m and method in ("PUT", "DELETE"):  # BUG-146: a file written straight into a branch
        branch = next((d.get("branch") for d in dicts if isinstance(d.get("branch"), str)), None)
        return Call("ref-write", host="github", repo=m.group(1), branch=branch, url=url, client=r.client)
    m = _AZ_PUSHES.search(path)
    if m and method == "POST":
        names = [d.get("name") for d in dicts if isinstance(d.get("name"), str) and d["name"].startswith("refs/")]
        heads = [n[len("refs/heads/"):] for n in names if n.startswith("refs/heads/")]
        return Call("ref-write", host="azure", repo=unquote(m.group(1)), url=url, client=r.client,
                    branch=heads[0] if len(heads) == 1 else None)
    m = _GL_REPO_WRITE.search(path)
    if m and method in ("POST", "PUT", "DELETE"):
        branch = next((d.get("branch") for d in dicts if isinstance(d.get("branch"), str)), None)
        return Call("ref-write", host="gitlab", repo=unquote(m.group(1)), branch=branch, url=url, client=r.client)
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


def _inline_hits(script):
    """An inline script that calls a completion/approval endpoint with a write (BUG-146: precedence, reads)."""
    if not script:
        return False
    called = _ENDPOINT_TEXT.search(script) or re.search(r"Invoke-(RestMethod|WebRequest)", script, re.I)
    return bool(called and (_COMPLETING_TEXT.search(script) or _WRITE_VERB.search(script) or
                            _GRAPHQL_WRITE.search(script)))


def inline_call(seg):
    """A ``fail`` :class:`Call` for an inline script (``-c``/``-e`` or a here-document) that calls a completion
    or approval endpoint."""
    opts = INLINE.get(posix_base(seg.argv0))
    if not opts:
        return None
    a = seg.argv[1:]
    scripts = [a[i + 1] for i, x in enumerate(a) if x in opts and i + 1 < len(a)]
    scripts += [getattr(rd, "body", None) or "" for rd in seg.redirects if rd.op in ("<<", "<<-", "<<<")]
    if any(_inline_hits(sc) for sc in scripts):
        return Call("fail", client=seg.argv0,
                    reason="an inline %s script calls a PR completion or approval endpoint, which the gate cannot "
                           "read; send the request with curl, gh, az or glab instead" % posix_base(seg.argv0))
    return None


def posix_base(name):
    return (name or "").rsplit("/", 1)[-1]


TEXT_ONLY = frozenset({"echo", "printf", "cat", "grep", "egrep", "rg", "less", "more", "head", "tail", "sed", "awk",
                       "tee", "jq", "true", ":"})
_NET_SINK = re.compile(r"\b(openssl|s_client|nc|ncat|netcat|socat|telnet)\b|/dev/(tcp|udp)/")


def unknown_client_call(seg, raw=None):
    """BUG-146: a command this module does not parse that names a completion/approval endpoint URL together
    with a write method fails closed."""
    args = seg.argv[1:]
    if posix_base(seg.argv0) in TEXT_ONLY and not _NET_SINK.search(raw or ""):
        return None  # text output: a request only when the call sends it to a socket
    urls = [u for u in args if _URL_TOKEN.match(u) and _ENDPOINT_TEXT.search(unquote(u))]
    if not urls:  # raw HTTP written by hand (printf "PUT /repos/…/pulls/12/merge HTTP/1.1" | openssl s_client)
        raw = [x for x in args if re.search(r"(?i)\b(PUT|PATCH|POST|DELETE)\s+/\S+", x) and
               _ENDPOINT_TEXT.search(unquote(x))]
        if raw:
            return Call("fail", client=seg.argv0, reason="%s writes a raw HTTP request to a completion or approval "
                                                         "endpoint, which the gate cannot verify" % posix_base(seg.argv0))
        return None
    joined = " ".join(args)
    if re.search(r"(?i)(^|\s)(PUT|PATCH|POST|DELETE)(\s|$)", joined) or re.search(
            r"(?i)(-X|--request|-m|--method)[= ]?\s*(PUT|PATCH|POST|DELETE)", joined):
        return Call("fail", client=seg.argv0, url=urls[0],
                    reason="%s sends a write to %s, which the gate cannot read; use curl, gh, az or glab"
                           % (posix_base(seg.argv0), urls[0].split("?")[0]))
    return None


def classify_segment(seg, raw=None):
    """The :class:`Call` of one segment (HTTP client or inline script), or None."""
    if not seg.argv:
        return None
    c = inline_call(seg)
    if c is not None:
        return c
    r = parse_request(seg)
    if r is None:
        if posix_base(seg.argv0) in ("git", "gh", "glab", "az"):
            return None
        return unknown_client_call(seg, raw)
    return classify(r)
