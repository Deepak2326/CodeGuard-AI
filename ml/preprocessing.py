"""Shared, string-aware normalization. Never executes input."""
import re

TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
IDENTIFIER = re.compile(r'\b(?:CWE\d+\w*|bad\w*|good\w*)\b')

def strip_comments(code: str) -> str:
    return TOKENS.sub(lambda m: " " if m[0].startswith(("//", "/*")) else m[0], code)

def normalize(code: str) -> str:
    code = strip_comments(code).replace("\r\n", "\n")
    code = IDENTIFIER.sub("function", code)
    # Juliet uses public bad methods and private/static good helpers. Remove that label cue.
    code = re.sub(r'\b(?:(?:public|private|protected|static)\s+)+(?=void\b)', '', code)
    code = re.sub(r"^\s*#(?:ifn?def|endif).*?$", " ", code, flags=re.M)
    return re.sub(r"\s+", " ", code).strip()
