def escape_chars(path: str) -> str:
    return path.replace('<', '--lt--').replace('>', '--gt--').replace('\\', '--bs--')


def escaped_file_path(path: str, suffix: str) -> str:
    """`path` with its characters escaped (`escape_chars`), ending with `suffix`"""
    path = escape_chars(path)
    return path if path.endswith(suffix) else path + suffix


def unescape_chars(path: str) -> str:
    return path.replace('--lt--', '<').replace('--gt--', '>').replace('--bs--', '\\')
