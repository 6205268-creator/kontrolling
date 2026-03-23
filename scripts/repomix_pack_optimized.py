"""
Сборка repomix-output.txt: компактный дамп исходников (цель ≤ ~10 МБ).

Исключения папок + лимит на файл + пропуск бинарников и mcp.json с секретами.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "repomix-output.txt")

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".qwen",
    "obsidian",
    # тяжёлые / не исходный код
    "venv",
    ".venv",
    "docs/source-material",
    "playwright-report",
    "htmlcov",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "kontrolling-scenarios",
}

SKIP_NAMES = {"repomix-output.txt", "repomix-output.xml"}

# Не встраивать (секреты / не нужно в дампе)
SKIP_EXACT_NAMES = {"mcp.json"}

SKIP_EXT = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".db",
    ".dbf",
    ".exe",
    ".dll",
    ".pyd",
    ".so",
    ".dylib",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".docx",
    ".ibx",
    ".ibl",
}
SKIP_EXT_LOWER = {e.lower() for e in SKIP_EXT}

# Макс. размер содержимого одного файла в дампе (байты UTF-8), ~12–14 КБ текста
MAX_CONTENT_BYTES = 14_000


def should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def is_skipped_file(_rel_posix: str, basename: str) -> bool:
    if basename in SKIP_NAMES or basename in SKIP_EXACT_NAMES:
        return True
    ext = os.path.splitext(basename.lower())[1]
    return ext in SKIP_EXT_LOWER


def try_decode(raw: bytes) -> tuple[str | None, bool]:
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return raw.decode(enc), False
        except UnicodeDecodeError:
            continue
    return None, True


def main() -> None:
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if is_skipped_file(rel, fn):
                continue
            files.append(full)

    files.sort(key=lambda p: p.lower())
    sep = "=" * 80
    truncated_files = 0

    with open(OUT, "w", encoding="utf-8", newline="\n") as out:
        out.write(f"# Optimized repomix: {ROOT}\n")
        out.write(f"# Excluded dirs: {sorted(EXCLUDE_DIRS)}\n")
        out.write(f"# Max content bytes per file: {MAX_CONTENT_BYTES}\n")
        out.write(f"# Total files: {len(files)}\n\n")

        for full in files:
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            out.write(sep + "\n")
            out.write(f"FILE: {rel}\n")
            out.write(sep + "\n")

            try:
                file_size = os.path.getsize(full)
            except OSError:
                out.write("[SKIPPED: unreadable]\n\n")
                continue

            to_read = min(file_size, MAX_CONTENT_BYTES + 1)
            with open(full, "rb") as bf:
                raw = bf.read(to_read)

            if b"\x00" in raw[: min(len(raw), 8192)]:
                out.write("[SKIPPED: binary]\n\n")
                continue

            truncated = file_size > MAX_CONTENT_BYTES
            if truncated:
                raw = raw[:MAX_CONTENT_BYTES]
                truncated_files += 1

            text, failed = try_decode(raw)
            if failed or text is None:
                out.write("[SKIPPED: not decodable as text]\n\n")
                continue

            out.write(text)
            if truncated:
                out.write(
                    f"\n\n[TRUNCATED: file was {file_size} bytes, "
                    f"first {MAX_CONTENT_BYTES} bytes shown]\n"
                )
            elif text and not text.endswith("\n"):
                out.write("\n")
            out.write("\n")

        out.write(f"\n# Files with truncation: {truncated_files}\n")

    out_size = os.path.getsize(OUT)
    print("Written:", OUT)
    print("Files:", len(files))
    print(f"Output size: {out_size / 1024 / 1024:.2f} MB")
    if out_size > 10 * 1024 * 1024:
        print("WARNING: still over 10 MB — lower MAX_CONTENT_BYTES or exclude more dirs.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
