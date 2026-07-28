#!/usr/bin/env python3
"""
Workspace manifest for the release tools.

Every path used by the release tools comes from a manifest file passed on the
command line. Nothing is resolved relative to this script, and no absolute
user-specific path is ever stored: manifest entries are relative to a workspace
root, which is either given with ``--workspace`` or defaults to the directory
containing the manifest.

The manifest is TOML. Python 3.11+ parses it with the standard library; on
older interpreters the tools fall back to the small subset parser below, which
covers exactly the constructs used by ``copies.example.toml``:

    # comment
    key = "basic string"        (escapes: \\\\  \\"  \\n  \\t)
    key = 'literal string'      (no escapes -- use for regexes)
    key = 123
    key = true | false
    key = ["a", "b"]
    [table]
    [[array_of_tables]]

Anything outside that subset raises rather than being silently ignored.
"""
import os
import re

__all__ = ["load", "ManifestError", "parse_toml", "read_text", "read_bytes"]

def read_text(path, errors="strict"):
    with open(path, encoding="utf-8", errors=errors) as fh:
        return fh.read()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()



class ManifestError(RuntimeError):
    pass


# ── minimal TOML subset ─────────────────────────────────────────────────────
def _value(raw, lineno):
    raw = raw.strip()
    if raw.startswith("'"):
        if not raw.endswith("'") or len(raw) < 2:
            raise ManifestError(f"line {lineno}: unterminated literal string")
        return raw[1:-1]
    if raw.startswith('"'):
        if not raw.endswith('"') or len(raw) < 2:
            raise ManifestError(f"line {lineno}: unterminated string")
        body = raw[1:-1]
        for a, b in (("\\\\", "\x00"), ('\\"', '"'), ("\\n", "\n"), ("\\t", "\t")):
            body = body.replace(a, b)
        return body.replace("\x00", "\\")
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ManifestError(f"line {lineno}: unterminated array")
        inner = raw[1:-1].strip()
        if not inner:
            return []
        # split on commas that are not inside quotes
        out, buf, q = [], "", None
        for ch in inner:
            if q:
                buf += ch
                if ch == q:
                    q = None
            elif ch in "\"'":
                q = ch
                buf += ch
            elif ch == ",":
                out.append(buf)
                buf = ""
            else:
                buf += ch
        if buf.strip():
            out.append(buf)
        return [_value(x, lineno) for x in out if x.strip()]
    if raw in ("true", "false"):
        return raw == "true"
    if re.fullmatch(r"[+-]?\d+", raw):
        return int(raw)
    raise ManifestError(f"line {lineno}: unsupported value {raw!r}")


def _join_arrays(lines):
    """Fold multi-line arrays onto one logical line, preserving line numbers."""
    out, buf, start, depth = [], None, 0, 0
    for lineno, line in enumerate(lines, 1):
        if buf is None:
            stripped = line.split("#", 1)[0] if "[" in line and "=" in line else line
            depth = stripped.count("[") - stripped.count("]")
            if "=" in line and depth > 0:
                buf, start = line.rstrip(), lineno
                continue
            out.append((lineno, line))
        else:
            buf += " " + line.strip()
            depth += line.count("[") - line.count("]")
            if depth <= 0:
                out.append((start, buf))
                buf = None
    if buf is not None:
        raise ManifestError(f"line {start}: unterminated array")
    return out


def parse_toml(text):
    """Parse the documented TOML subset into nested dicts/lists."""
    doc, cur = {}, None
    for lineno, line in _join_arrays(text.splitlines()):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[["):
            if not s.endswith("]]"):
                raise ManifestError(f"line {lineno}: malformed table array header")
            name = s[2:-2].strip()
            doc.setdefault(name, [])
            if not isinstance(doc[name], list):
                raise ManifestError(f"line {lineno}: {name} is not a table array")
            cur = {}
            doc[name].append(cur)
            continue
        if s.startswith("["):
            if not s.endswith("]"):
                raise ManifestError(f"line {lineno}: malformed table header")
            name = s[1:-1].strip()
            cur = doc.setdefault(name, {})
            if not isinstance(cur, dict):
                raise ManifestError(f"line {lineno}: {name} is not a table")
            continue
        if "=" not in s:
            raise ManifestError(f"line {lineno}: expected key = value")
        k, v = s.split("=", 1)
        # strip trailing comments outside quotes
        v = v.strip()
        if v and v[0] not in "\"'[":
            v = v.split("#", 1)[0].strip()
        if cur is None:
            raise ManifestError(f"line {lineno}: key outside any table")
        cur[k.strip()] = _value(v, lineno)
    return doc


def _read(path):
    text = read_text(path)
    try:
        import tomllib                      # Python 3.11+
        return tomllib.loads(text)
    except ModuleNotFoundError:
        pass
    try:
        import tomli                        # optional backport
        return tomli.loads(text)
    except ModuleNotFoundError:
        return parse_toml(text)


class Manifest:
    def __init__(self, data, workspace, path):
        self.data = data
        self.workspace = workspace
        self.path = path

    def abs(self, rel):
        """Resolve a manifest-relative path against the workspace root."""
        return os.path.normpath(os.path.join(self.workspace, rel))

    def table(self, name):
        t = self.data.get(name)
        if not isinstance(t, dict):
            raise ManifestError(f"manifest is missing the [{name}] table")
        return t

    def array(self, name):
        a = self.data.get(name)
        if not isinstance(a, list) or not a:
            raise ManifestError(f"manifest is missing any [[{name}]] entries")
        return a

    def manuscripts(self):
        ms = self.array("manuscript")
        required = {"name", "tex", "figure_prefix", "bibliography", "abstract"}
        for m in ms:
            missing = required - set(m)
            if missing:
                raise ManifestError(
                    f"manuscript {m.get('name', '?')!r} is missing "
                    f"{', '.join(sorted(missing))}")
            if m["abstract"] not in ("env", "section"):
                raise ManifestError(
                    f"manuscript {m['name']!r}: abstract must be "
                    f"'env' or 'section', got {m['abstract']!r}")
        canon = [m for m in ms if m.get("canonical")]
        if len(canon) != 1:
            raise ManifestError(
                f"exactly one manuscript must set canonical = true "
                f"(found {len(canon)})")
        return ms, canon[0]


def load(manifest_path, workspace=None):
    if not manifest_path:
        raise ManifestError("a manifest is required (--manifest PATH)")
    manifest_path = os.path.abspath(manifest_path)
    if not os.path.exists(manifest_path):
        raise ManifestError(f"manifest not found: {manifest_path}")
    root = os.path.abspath(workspace) if workspace \
        else os.path.dirname(manifest_path)
    if not os.path.isdir(root):
        raise ManifestError(f"workspace root is not a directory: {root}")
    return Manifest(_read(manifest_path), root, manifest_path)


def add_common_args(parser):
    parser.add_argument("--manifest", required=True,
                        help="path to the workspace manifest (TOML)")
    parser.add_argument("--workspace", default=None,
                        help="workspace root; defaults to the manifest's directory")
