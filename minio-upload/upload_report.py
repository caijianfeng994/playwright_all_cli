from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit, urlparse

_LINK_ATTR_PATTERN = re.compile(
    r'(?P<attr>href|src)\s*=\s*(?P<quote>["\'])(?P<url>.*?)(?P=quote)',
    re.IGNORECASE,
)
_CSS_URL_PATTERN = re.compile(
    r"url\(\s*(?P<quote>[\"']?)(?P<url>.*?)(?P=quote)\s*\)",
    re.IGNORECASE,
)

_SENSITIVE_PATTERNS = (
    re.compile(r"Authorization\s*:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"Cookie\s*:\s*\S+", re.IGNORECASE),
    re.compile(r"password\s*(?:=|:)\s*\S+", re.IGNORECASE),
    re.compile(r'"access_token"\s*:\s*"[^"]+"', re.IGNORECASE),
    re.compile(
        r"""(?ix)
        (?<![A-Z0-9_])
        ["']?(?:
            access_key|secret_key|access_token|session_token|token|password
            |(?:MINIO|AWS)_(?:
                ACCESS_KEY(?:_ID)?|SECRET_KEY|SECRET_ACCESS_KEY
                |SESSION_TOKEN|SECURITY_TOKEN
                |TOKEN|PASSWORD
            )
        )["']?
        \s*(?:=|:)\s*
        (?:"[^"]+"|'[^']+'|[^\s,}\]]+)
        """
    ),
)


class UploadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ReportBundle:
    run_name: str
    report_dir: Path
    qa_dir: Path
    report_html: Path


@dataclass
class UploadResult:
    success: bool
    report_url: str | None
    expires_in: int
    bucket: str
    object_prefix: str
    report_object_name: str | None
    manifest_object_name: str | None
    uploaded_count: int
    failed_files: list[str]


def discover_bundle(report_path: Path) -> ReportBundle:
    report_path = report_path.resolve()
    report_dir = report_path if report_path.is_dir() else report_path.parent
    report_html = report_dir / "report.html"
    if not report_html.is_file():
        raise UploadError("REPORT_NOT_FOUND", f"report.html not found: {report_html}")
    reports_root = report_dir.parent
    if reports_root.name != "reports" or reports_root.parent.name != "web-output":
        raise UploadError("INVALID_REPORT_PATH", "report path must be under web-output/reports")
    qa_dir = reports_root.parent / "qa" / report_dir.name
    if not qa_dir.is_dir():
        raise UploadError("QA_EVIDENCE_NOT_FOUND", f"QA evidence directory not found: {qa_dir}")
    return ReportBundle(report_dir.name, report_dir, qa_dir.resolve(), report_html)


def build_object_name(bundle: ReportBundle, file_path: Path) -> str:
    file_path = file_path.resolve()
    for kind, root in (("reports", bundle.report_dir), ("qa", bundle.qa_dir)):
        if file_path.is_relative_to(root):
            relative = file_path.relative_to(root).as_posix()
            return f"web-ui-reports/{bundle.run_name}/{kind}/{bundle.run_name}/{relative}"
    raise UploadError("PATH_OUTSIDE_BUNDLE", f"outside report bundle: {file_path}")


def scan_sensitive_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SENSITIVE_PATTERNS)


def guess_content_type(file_path: Path) -> str:
    content_type, _ = mimetypes.guess_type(file_path.name)
    return content_type or "application/octet-stream"


def assert_safe_text_files(files: list[Path]) -> None:
    for file_path in files:
        try:
            text = file_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "\x00" in text:
            continue
        control_count = sum(
            ord(character) < 32 and character not in "\n\r\t"
            for character in text
        )
        if text and control_count / len(text) > 0.05:
            continue
        if scan_sensitive_text(text):
            raise UploadError(
                "SENSITIVE_DATA_FOUND",
                f"sensitive data found: {file_path}",
            )


def build_manifest(
    bundle: ReportBundle,
    uploaded: list[str],
    expires: timedelta,
) -> dict[str, object]:
    return {
        "run_name": bundle.run_name,
        "object_prefix": f"web-ui-reports/{bundle.run_name}",
        "uploaded_files": uploaded,
        "uploaded_count": len(uploaded),
        "expires_in": int(expires.total_seconds()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _upload_bundle(
    bundle: ReportBundle,
    client: type[Any],
    expires: timedelta,
) -> UploadResult:
    files = sorted(
        [
            path
            for root in (bundle.report_dir, bundle.qa_dir)
            for path in root.rglob("*")
            if path.is_file()
        ]
    )
    assert_safe_text_files(files)
    report_html = bundle.report_html.resolve()
    asset_files = [path for path in files if path.resolve() != report_html]
    uploaded: list[str] = []
    object_names = {
        file_path.resolve(): build_object_name(bundle, file_path)
        for file_path in files
    }
    urls = {
        file_path: client.get_presigned_url(object_name, expires)
        for file_path, object_name in object_names.items()
    }

    for file_path in asset_files:
        resolved_path = file_path.resolve()
        object_name = object_names[resolved_path]
        data = _prepare_upload_data(file_path, urls)
        client.upload_bytes(
            object_name,
            data,
            guess_content_type(file_path),
        )
        uploaded.append(object_name)

    report_object_name = object_names[report_html]
    client.upload_bytes(
        report_object_name,
        _prepare_upload_data(report_html, urls),
        "text/html; charset=utf-8",
    )
    uploaded.append(report_object_name)
    report_url = urls[report_html]
    manifest_object_name = (
        f"web-ui-reports/{bundle.run_name}/upload-manifest.json"
    )
    complete_uploaded = [*uploaded, manifest_object_name]
    manifest = build_manifest(bundle, complete_uploaded, expires)
    client.upload_bytes(
        manifest_object_name,
        json.dumps(manifest, ensure_ascii=False).encode(),
        "application/json",
    )
    return UploadResult(
        True,
        report_url,
        int(expires.total_seconds()),
        str(
            getattr(client, "bucket_name", None)
            or os.environ.get("MINIO_BUCKET", "qa-platform")
        ),
        f"web-ui-reports/{bundle.run_name}",
        report_object_name,
        manifest_object_name,
        len(complete_uploaded),
        [],
    )


def upload_bundle(
    bundle: ReportBundle,
    client: type[Any],
    expires: timedelta,
) -> UploadResult:
    try:
        return _upload_bundle(bundle, client, expires)
    except UploadError:
        raise
    except Exception as error:
        raise UploadError("UPLOAD_FAILED", "report bundle upload failed") from error


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UploadError("INVALID_ARGUMENT", "invalid command arguments")


def _expiration_hours(value: str) -> int:
    try:
        hours = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expires-hours must be an integer") from error
    if not 1 <= hours <= 168:
        raise argparse.ArgumentTypeError("expires-hours must be between 1 and 168")
    return hours


def _load_minio_dependencies() -> type[Any]:
    from minio_client import MinIOClient

    return MinIOClient


def _public_error_message(code: str) -> str:
    messages = {
        "DEPENDENCY_UNAVAILABLE": "MinIO dependency unavailable",
        "INVALID_ARGUMENT": "invalid command arguments",
        "EXECUTION_FAILED": "report upload execution failed",
        "UPLOAD_FAILED": "report bundle upload failed",
        "SENSITIVE_DATA_FOUND": "sensitive data found in report bundle",
        "UNRESOLVED_REPORT_LINKS": "unresolved local report links",
        "REPORT_NOT_FOUND": "report not found",
        "INVALID_REPORT_PATH": "invalid report path",
        "QA_EVIDENCE_NOT_FOUND": "QA evidence not found",
    }
    return messages.get(code, "report upload failed")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    try:
        parser = _JsonArgumentParser(description="上传 Web UI 测试报告到 MinIO")
        parser.add_argument("report_path", type=Path)
        parser.add_argument(
            "--expires-hours",
            type=_expiration_hours,
            default=24,
        )
        args = parser.parse_args(argv)
        try:
            client = _load_minio_dependencies()
        except Exception as error:
            raise UploadError(
                "DEPENDENCY_UNAVAILABLE",
                "MinIO dependency unavailable",
            ) from error
        bundle = discover_bundle(args.report_path)
        result = upload_bundle(
            bundle,
            client,
            timedelta(hours=args.expires_hours),
        )
        payload: dict[str, object] = asdict(result)
        exit_code = 0
    except UploadError as error:
        payload = {
            "success": False,
            "error_code": error.code,
            "error": _public_error_message(error.code),
        }
        logging.error("UPLOAD_ERROR code=%s", error.code)
        exit_code = 1
    except Exception:
        logging.error("UPLOAD_ERROR code=EXECUTION_FAILED")
        payload = {
            "success": False,
            "error_code": "EXECUTION_FAILED",
            "error": _public_error_message("EXECUTION_FAILED"),
        }
        exit_code = 1

    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return exit_code


def _split_local_url(url: str) -> tuple[str, str, str]:
    fragment = ""
    if "#" in url:
        url, fragment = url.split("#", 1)
    query = ""
    if "?" in url:
        url, query = url.split("?", 1)
    return url, query, fragment


def _merge_presigned_url(presigned: str, fragment: str) -> str:
    parsed = urlsplit(presigned)
    merged_fragment = fragment or parsed.fragment
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, merged_fragment))


def _is_external_url(url: str) -> bool:
    if not url or url.startswith("#"):
        return True
    if url.startswith("//"):
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https", "data", "mailto"}


def rewrite_html_links(
    html: str,
    report_html: Path,
    mapping: dict[Path, str],
) -> tuple[str, list[str]]:
    base_dir = report_html.resolve().parent
    unresolved: list[str] = []

    def replace_match(match: re.Match[str]) -> str:
        attr = match.group("attr")
        quote = match.group("quote")
        url = match.group("url")
        if _is_external_url(url):
            return match.group(0)
        path_part, _query, fragment = _split_local_url(url)
        resolved = (base_dir / path_part).resolve()
        presigned = mapping.get(resolved)
        if presigned is None:
            unresolved.append(url)
            return match.group(0)
        merged = _merge_presigned_url(presigned, fragment)
        return f"{attr}={quote}{merged}{quote}"

    rewritten = _LINK_ATTR_PATTERN.sub(replace_match, html)
    return rewritten, unresolved


def rewrite_css_links(
    css: str,
    css_file: Path,
    mapping: dict[Path, str],
) -> tuple[str, list[str]]:
    base_dir = css_file.resolve().parent
    unresolved: list[str] = []

    def replace_match(match: re.Match[str]) -> str:
        quote = match.group("quote")
        url = match.group("url")
        if _is_external_url(url):
            return match.group(0)
        path_part, _query, fragment = _split_local_url(url)
        resolved = (base_dir / path_part).resolve()
        presigned = mapping.get(resolved)
        if presigned is None:
            unresolved.append(url)
            return match.group(0)
        merged = _merge_presigned_url(presigned, fragment)
        return f"url({quote}{merged}{quote})"

    rewritten = _CSS_URL_PATTERN.sub(replace_match, css)
    return rewritten, unresolved


def _prepare_upload_data(
    file_path: Path,
    mapping: dict[Path, str],
) -> bytes:
    suffix = file_path.suffix.lower()
    if suffix not in {".html", ".htm", ".css"}:
        return file_path.read_bytes()

    source = file_path.read_text(encoding="utf-8")
    if suffix in {".html", ".htm"}:
        rewritten, unresolved = rewrite_html_links(source, file_path, mapping)
    else:
        rewritten, unresolved = rewrite_css_links(source, file_path, mapping)
    if unresolved:
        raise UploadError("UNRESOLVED_REPORT_LINKS", ", ".join(unresolved))
    return rewritten.encode("utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
