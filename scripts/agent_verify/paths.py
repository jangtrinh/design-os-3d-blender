"""Path resolution for the verify lib. No hardcoded machine paths."""
import hashlib
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def repo_root():
    """Walk up from this package, else $AGENT_REPO_ROOT, else cwd."""
    d = _HERE
    while True:
        if (os.path.isdir(os.path.join(d, "scripts"))
                and os.path.isdir(os.path.join(d, "knowledge"))):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.environ.get("AGENT_REPO_ROOT") or os.getcwd()


def out_dir(env_var, *parts):
    """Output directory: $env_var if set, else <repo>/<parts>. Created."""
    d = os.environ.get(env_var) or os.path.join(repo_root(), *parts)
    os.makedirs(d, exist_ok=True)
    return d


def lib_sha(extra=None):
    """8-hex fingerprint of the package sources (+ the facade when known)."""
    h = hashlib.sha256()
    files = sorted(os.path.join(_HERE, f) for f in os.listdir(_HERE)
                   if f.endswith(".py"))
    if extra and os.path.isfile(extra):
        files.append(extra)
    for f in files:
        try:
            with open(f, "rb") as fh:
                h.update(fh.read())
        except OSError:
            return "unknown"
    return h.hexdigest()[:8]
