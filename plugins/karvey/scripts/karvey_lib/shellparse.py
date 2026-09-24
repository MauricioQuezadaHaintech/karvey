"""Shell segmentation for the guards (architecture §3.4 "Shell segmentation", nothing more).

``parse(command, cwd)`` splits a Bash tool command into **segments** — the simple commands the
guards classify — and resolves, per segment, the directory it runs in and its git target:

- separators ``;`` ``&&`` ``||`` ``|`` ``|&`` ``&`` newlines and ``( )`` split segments; quotes,
  escapes, comments and heredoc bodies are respected (a heredoc body is data, never a segment);
- leading ``VAR=val`` assignments and the wrappers ``command builtin exec time nohup env sudo``
  (plus ``nice timeout stdbuf``, which wrap the same way) are stripped; a leading ``\\`` and an
  absolute path (``/usr/bin/gh``) are normalised to the command name; shell keywords at command
  position (``if then do { !`` …) are skipped;
- the script of ``bash|sh|zsh|dash|ksh -c '…'``, the arguments of ``eval`` and the contents of
  ``$(…)`` and backticks are parsed recursively, to depth 3 (deeper → ``unparsed``);
- ``cd``/``pushd <dir>`` changes the directory of the later segments (not across a pipe), relative
  to the payload ``cwd``; ``~`` and ``$HOME`` are expanded, any other variable leaves the
  directory unresolved (``None``);
- ``git`` global options are parsed: ``-C`` (cumulative), ``-c k=v``, ``--git-dir``,
  ``--work-tree``, ``--no-pager`` …, and ``GIT_DIR`` / ``GIT_WORK_TREE`` assignments;
- redirections are recorded per segment as ``(op, fd, target)`` so the plan-gate can tell a write
  (``> notes.txt``) from a stream redirection (``2>/dev/null``, ``2>&1``) — REQ-W1-014;
- unbalanced quotes, parentheses or backticks mark the whole input ``unparsed``: each guard then
  applies its own fail mode (§3.2).

A hand-written lexer is used instead of ``shlex``: ``shlex`` cannot tell ``2>/dev/null`` from
``2 > /dev/null`` nor report where ``$(…)`` starts, and both matter here. Standard library only.
"""
import os
import posixpath
import re

MAX_DEPTH = 3
SHELLS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})
KEYWORDS = frozenset({"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "!", "{", "}"})
_OPS = ("&&", "||", ";;", "|&", ";", "|", "&", "(", ")")
_REDIRS = ("&>>", "<<<", "<<-", "<<", ">>", ">|", ">&", "<&", "<>", "&>", ">", "<")
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_VAR = re.compile(r"\$(\{[^}]*\}|[A-Za-z_][A-Za-z0-9_]*|.)")


class Unparsable(Exception):
    pass


class Word:
    __slots__ = ("text", "raw", "quoted", "exp", "subs")

    def __init__(self):
        self.text, self.raw, self.quoted, self.exp, self.subs = "", "", False, False, []

    def __repr__(self):
        return "Word(%r)" % self.text


class Redirect:
    __slots__ = ("op", "fd", "target", "word", "body")

    def __init__(self, op, fd):
        self.op, self.fd, self.target, self.word, self.body = op, fd, None, None, None

    def as_tuple(self):
        return (self.op, self.fd, self.target)

    def __repr__(self):
        return "Redirect%r" % (self.as_tuple(),)


class Segment:
    """One simple command. ``argv`` is quote-removed text with wrappers and assignments stripped."""

    __slots__ = ("argv", "argv0", "words", "assignments", "wrappers", "redirects", "op", "cwd", "depth",
                 "source", "git", "unresolved", "raw")

    def __init__(self):
        self.argv, self.argv0, self.words, self.assignments = [], None, [], {}
        self.wrappers, self.redirects, self.op, self.cwd = [], [], "", None
        self.depth, self.source, self.git, self.unresolved, self.raw = 0, "top", None, False, ""

    def __repr__(self):
        return "Segment(%r, cwd=%r, depth=%d, source=%s)" % (self.argv, self.cwd, self.depth, self.source)


class Parsed:
    __slots__ = ("segments", "unparsed", "reasons", "raw")

    def __init__(self, raw):
        self.segments, self.unparsed, self.reasons, self.raw = [], False, [], raw


# --------------------------------------------------------------------------- lexer
def _read_paren(s, i):
    """``s[i:]`` starts just after ``$(``; return (inner, index after the closing paren)."""
    depth, j, n = 1, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "'":
            k = s.find("'", j + 1)
            if k < 0:
                raise Unparsable("unbalanced quote inside $( )")
            j = k + 1
            continue
        if c == '"':
            j = _skip_dquote(s, j + 1)
            continue
        if c == "`":
            _, j = _read_backtick(s, j + 1)
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return s[i:j], j + 1
        j += 1
    raise Unparsable("unbalanced $( )")


def _skip_dquote(s, j):
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            return j + 1
        if c == "$" and s.startswith("$(", j):
            _, j = _read_paren(s, j + 2)
            continue
        if c == "`":
            _, j = _read_backtick(s, j + 1)
            continue
        j += 1
    raise Unparsable("unbalanced double quote")


def _read_backtick(s, i):
    j, n, out = i, len(s), []
    while j < n:
        c = s[j]
        if c == "\\" and j + 1 < n and s[j + 1] in "`\\$":
            out.append(s[j + 1])
            j += 2
            continue
        if c == "`":
            return "".join(out), j + 1
        out.append(c)
        j += 1
    raise Unparsable("unbalanced backtick")


def lex(s):
    """Tokens: ``("word", Word)`` · ``("op", op)`` · ``("redir", Redirect)``. Raises Unparsable."""
    tokens = []
    i, n = 0, len(s)
    w = None
    heredocs = []  # (Redirect, strip_tabs) waiting for the next newline

    def start():
        nonlocal w
        if w is None:
            w = Word()
            w_start[0] = i
        return w

    w_start = [0]

    def flush(end):
        nonlocal w
        if w is not None:
            w.raw = s[w_start[0]:end]
            if tokens and tokens[-1][0] == "redir" and tokens[-1][1].word is None:
                tokens[-1][1].word, tokens[-1][1].target = w, w.text  # a heredoc needs its delimiter now
            tokens.append(("word", w))
            w = None

    while i < n:
        c = s[i]
        if c in " \t":
            flush(i)
            i += 1
            continue
        if c == "\\":
            if i + 1 < n and s[i + 1] == "\n":
                i += 2
                continue
            cur = start()
            cur.quoted = True
            if i + 1 < n:
                cur.text += s[i + 1]
            i += 2
            continue
        if c == "'":
            k = s.find("'", i + 1)
            if k < 0:
                raise Unparsable("unbalanced single quote")
            cur = start()
            cur.quoted = True
            cur.text += s[i + 1:k]
            i = k + 1
            continue
        if c == '"':
            cur = start()
            cur.quoted = True
            j = i + 1
            while True:
                if j >= n:
                    raise Unparsable("unbalanced double quote")
                d = s[j]
                if d == "\\" and j + 1 < n and s[j + 1] in '$`"\\\n':
                    if s[j + 1] != "\n":
                        cur.text += s[j + 1]
                    j += 2
                    continue
                if d == '"':
                    j += 1
                    break
                if d == "$" and s.startswith("$(", j) and not s.startswith("$((", j):
                    inner, k = _read_paren(s, j + 2)
                    cur.subs.append(inner)
                    cur.exp = True
                    cur.text += s[j:k]
                    j = k
                    continue
                if d == "`":
                    inner, k = _read_backtick(s, j + 1)
                    cur.subs.append(inner)
                    cur.exp = True
                    cur.text += s[j:k]
                    j = k
                    continue
                if d == "$":
                    cur.exp = True
                cur.text += d
                j += 1
            i = j
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            cur = start()
            cur.exp = True
            if s.startswith("$((", i):
                _, k = _read_paren(s, i + 2)  # arithmetic: not a command
            else:
                inner, k = _read_paren(s, i + 2)
                cur.subs.append(inner)
            cur.text += s[i:k]
            i = k
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "{":
            k = s.find("}", i + 2)
            if k < 0:
                raise Unparsable("unbalanced ${")
            cur = start()
            cur.exp = True
            cur.text += s[i:k + 1]
            i = k + 1
            continue
        if c == "$":
            cur = start()
            cur.exp = True
            cur.text += c
            i += 1
            continue
        if c == "`":
            inner, k = _read_backtick(s, i + 1)
            cur = start()
            cur.exp = True
            cur.subs.append(inner)
            cur.text += s[i:k]
            i = k
            continue
        if c == "#" and w is None:
            k = s.find("\n", i)
            i = n if k < 0 else k
            continue
        if c == "\n":
            flush(i)
            tokens.append(("op", "\n"))
            i += 1
            for rd, strip in heredocs:
                body = []
                while i < n:
                    k = s.find("\n", i)
                    line = s[i:] if k < 0 else s[i:k]
                    i = n if k < 0 else k + 1
                    cmp = line.lstrip("\t") if strip else line
                    if cmp == (rd.target or ""):
                        break
                    body.append(line)
                rd.body = "\n".join(body)
            heredocs = []
            continue
        if s.startswith("&&", i) or s.startswith("||", i):
            flush(i)
            tokens.append(("op", s[i:i + 2]))
            i += 2
            continue
        red = next((r for r in _REDIRS if s.startswith(r, i)), None)
        if red is not None:
            fd = None
            if w is not None and w.text.isdigit() and not w.quoted and not w.exp and red[0] in "<>":
                fd = w.text
                w = None
            else:
                flush(i)
            rd = Redirect(red, fd)
            tokens.append(("redir", rd))
            if red in ("<<", "<<-"):
                heredocs.append((rd, red == "<<-"))
            i += len(red)
            continue
        op = next((o for o in _OPS if s.startswith(o, i)), None)
        if op is not None:
            flush(i)
            tokens.append(("op", op))
            i += len(op)
            continue
        cur = start()
        cur.text += c
        i += 1
    flush(n)
    return tokens


# --------------------------------------------------------------------------- expansion
def expand(word, home=None):
    """The value of ``word`` as a path argument: ``~`` and ``$HOME`` expanded; None if any other
    expansion is left (an unresolved variable or a substitution)."""
    if word is None:
        return None
    home = home if home is not None else os.path.expanduser("~")
    text = word.text
    if not word.quoted and (text == "~" or text.startswith("~/")):
        text = home + text[1:]
    if not word.exp:
        return text
    text = text.replace("${HOME}", home).replace("$HOME", home)
    if "$" in text or "`" in text:
        return None
    return text


def _join(base, path):
    if path is None or base is None and not (path or "").startswith("/"):
        return None
    if path.startswith("/"):
        return posixpath.normpath(path)
    return posixpath.normpath(posixpath.join(base, path))


# --------------------------------------------------------------------------- segments
def _split(tokens):
    """Group tokens into raw segments: ``(op_before, [tokens])``."""
    segs, cur, op = [], [], ""
    for t in tokens:
        if t[0] == "op":
            segs.append((op, cur))
            cur, op = [], t[1]
        else:
            cur.append(t)
    segs.append((op, cur))
    return segs


def _strip_wrappers(words, assignments, wrappers):
    """Strip leading keywords, assignments and wrappers; returns (words, env_chdir)."""
    chdir = None
    changed = True
    while words and changed:
        changed = False
        while words and (words[0].text in KEYWORDS and not words[0].quoted):
            words = words[1:]
            changed = True
        while words and _ASSIGN.match(words[0].raw):
            name, _, _ = words[0].text.partition("=")
            assignments[name] = words[0].text[len(name) + 1:]
            words = words[1:]
            changed = True
        if not words:
            break
        name = _name(words[0].text)
        rest = words[1:]
        if name == "command":
            if any(x.text in ("-v", "-V") for x in rest[:2]):
                break  # `command -v x` is a lookup, not an execution of x
            while rest and rest[0].text == "-p":
                rest = rest[1:]
        elif name in ("builtin", "nohup"):
            pass
        elif name == "exec":
            while rest and rest[0].text.startswith("-"):
                rest = rest[2:] if rest[0].text == "-a" else rest[1:]
        elif name == "time":
            while rest and rest[0].text in ("-p", "--"):
                rest = rest[1:]
        elif name == "env":
            while rest:
                t = rest[0].text
                if t in ("-u", "--unset", "-S", "--split-string"):
                    rest = rest[2:]
                elif t in ("-C", "--chdir"):
                    chdir = rest[1] if len(rest) > 1 else None
                    rest = rest[2:]
                elif t.startswith("--chdir="):
                    w = Word()
                    w.text = t[len("--chdir="):]
                    chdir = w
                    rest = rest[1:]
                elif t == "--":
                    rest = rest[1:]
                    break
                elif t.startswith("-"):
                    rest = rest[1:]
                elif _ASSIGN.match(rest[0].raw):
                    n_, _, _ = t.partition("=")
                    assignments[n_] = t[len(n_) + 1:]
                    rest = rest[1:]
                else:
                    break
        elif name == "sudo":
            with_arg = {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "-T", "--user", "--group"}
            while rest and rest[0].text.startswith("-"):
                t = rest[0].text
                rest = rest[1:]
                if t == "--":
                    break
                if t in with_arg:
                    rest = rest[1:]
        elif name == "nice":
            while rest and rest[0].text.startswith("-"):
                rest = rest[2:] if rest[0].text in ("-n", "--adjustment") else rest[1:]
        elif name == "timeout":
            while rest and rest[0].text.startswith("-"):
                rest = rest[2:] if rest[0].text in ("-s", "--signal", "-k", "--kill-after") else rest[1:]
            rest = rest[1:]  # the duration
        elif name == "stdbuf":
            while rest and rest[0].text.startswith("-"):
                rest = rest[2:] if rest[0].text in ("-i", "-o", "-e") else rest[1:]
        else:
            break
        wrappers.append(name)
        words = rest
        changed = True
    return words, chdir


def _name(text):
    t = text.lstrip("\\")
    if "/" in t:
        t = t.rstrip("/").rsplit("/", 1)[-1]
    return t


_GIT_FLAGS = {"--no-pager", "--paginate", "-p", "-P", "--bare", "--no-replace-objects", "--literal-pathspecs",
              "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs", "--no-optional-locks",
              "--no-advice", "--exec-path"}
_GIT_WITH_ARG = {"--namespace", "--super-prefix", "--config-env", "--list-cmds", "--attr-source"}


def _parse_git(seg, words, home):
    """Global options of ``git`` → ``seg.git``."""
    info = {"sub": None, "args": [], "dir": seg.cwd, "unresolved": seg.cwd is None, "git_dir": None,
            "work_tree": None, "config": [], "no_pager": False}
    if "GIT_DIR" in seg.assignments:
        info["git_dir"] = seg.assignments["GIT_DIR"]
    if "GIT_WORK_TREE" in seg.assignments:
        info["work_tree"] = seg.assignments["GIT_WORK_TREE"]
    i = 1
    while i < len(words):
        w = words[i]
        t = w.text
        if t == "-C" and i + 1 < len(words):
            val = expand(words[i + 1], home)
            info["dir"] = _join(info["dir"], val) if val is not None else None
            if info["dir"] is None:
                info["unresolved"] = True
            i += 2
            continue
        if t == "-c" and i + 1 < len(words):
            info["config"].append(words[i + 1].text)
            i += 2
            continue
        if t.startswith("-c") and len(t) > 2 and "=" in t:
            info["config"].append(t[2:])
            i += 1
            continue
        if t in ("--git-dir", "--work-tree") and i + 1 < len(words):
            info[t[2:].replace("-", "_")] = expand(words[i + 1], home) or words[i + 1].text
            i += 2
            continue
        if t.startswith("--git-dir=") or t.startswith("--work-tree="):
            k, _, v = t.partition("=")
            info[k[2:].replace("-", "_")] = v
            i += 1
            continue
        if t in _GIT_FLAGS or t.startswith("--exec-path="):
            if t == "--no-pager":
                info["no_pager"] = True
            i += 1
            continue
        if t in _GIT_WITH_ARG:
            i += 2
            continue
        if any(t.startswith(x + "=") for x in _GIT_WITH_ARG):
            i += 1
            continue
        if t in ("--version", "--help", "-h", "--html-path", "--man-path", "--info-path"):
            break
        info["sub"] = t
        info["args"] = [x.text for x in words[i + 1:]]
        break
    for key in ("git_dir", "work_tree"):
        v = info[key]
        if isinstance(v, str) and v and not v.startswith("/") and info["dir"]:
            info[key] = posixpath.normpath(posixpath.join(info["dir"], v))
    return info


def _shell_script(words):
    """The script argument of ``bash -c …`` (combined short options such as ``-lc`` count)."""
    has_c = False
    i = 1
    while i < len(words):
        t = words[i].text
        if t == "--":
            i += 1
            break
        if t.startswith("--"):
            i += 1
            continue
        if t.startswith("-") and len(t) > 1:
            if "c" in t[1:]:
                has_c = True
            if t in ("-o", "+o", "-O", "+O"):
                i += 2
                continue
            i += 1
            continue
        break
    if has_c and i < len(words):
        return words[i].text
    return None


def parse(command, cwd=None, home=None, _depth=0, _source="top"):
    """Parse a Bash command into a :class:`Parsed` (never raises)."""
    res = Parsed(command if isinstance(command, str) else "")
    if not isinstance(command, str) or not command.strip():
        return res
    if _depth > MAX_DEPTH:
        res.unparsed = True
        res.reasons.append("nested deeper than %d levels" % MAX_DEPTH)
        return res
    home = home if home is not None else os.path.expanduser("~")
    try:
        tokens = lex(command)
    except Unparsable as exc:
        res.unparsed = True
        res.reasons.append(str(exc))
        return res
    raw_segs = _split(tokens)
    cur_dir = cwd
    for idx, (op, toks) in enumerate(raw_segs):
        next_op = raw_segs[idx + 1][0] if idx + 1 < len(raw_segs) else ""
        seg = Segment()
        seg.op, seg.depth, seg.source = op, _depth, _source
        words = []
        pending = None
        for t in toks:
            if t[0] == "redir":
                pending = t[1]
                seg.redirects.append(pending)
            elif pending is not None:
                pending.word = t[1]
                pending.target = t[1].text
                pending = None
            else:
                words.append(t[1])
        if not words and not seg.redirects:
            continue
        seg.words = list(words)
        seg.raw = " ".join(w.raw for w in words)
        words, chdir = _strip_wrappers(words, seg.assignments, seg.wrappers)
        if not words and not seg.redirects and not seg.assignments:
            continue  # a bare keyword such as `fi` or `done`
        seg.cwd = cur_dir
        if chdir is not None:
            seg.cwd = _join(cur_dir, expand(chdir, home))
        seg.argv = [w.text for w in words]
        seg.argv0 = _name(words[0].text) if words else None
        seg.unresolved = any(w.exp for w in words)
        if seg.argv0 == "git":
            seg.git = _parse_git(seg, words, home)
        res.segments.append(seg)

        # recursion: sh -c, eval, substitutions
        inner_scripts = []
        if seg.argv0 in SHELLS:
            script = _shell_script(words)
            if script is not None:
                inner_scripts.append((script, "shell-c"))
        elif seg.argv0 == "eval" and len(words) > 1:
            inner_scripts.append((" ".join(w.text for w in words[1:]), "eval"))
        for w in seg.words + [r.word for r in seg.redirects if r.word is not None]:
            for sub in w.subs:
                inner_scripts.append((sub, "subst"))
        for script, source in inner_scripts:
            sub = parse(script, cwd=seg.cwd, home=home, _depth=_depth + 1, _source=source)
            res.segments.extend(sub.segments)
            if sub.unparsed:
                res.unparsed = True
                res.reasons.extend(sub.reasons)

        # cd / pushd change the directory of later segments (not across a pipe)
        if seg.argv0 in ("cd", "pushd", "popd") and op not in ("|", "|&") and next_op not in ("|", "|&"):
            args = [w for w in words[1:] if not (w.text.startswith("-") and w.text != "-")]
            if seg.argv0 == "popd":
                cur_dir = None
            elif not args:
                cur_dir = home
            elif args[0].text == "-":
                cur_dir = None
            else:
                cur_dir = _join(cur_dir, expand(args[0], home))
    return res
