"""
MinIO 对象存储客户端

管理 MinIO 的连接和操作
"""

import io
import importlib.util
import json
import logging
import sys
from datetime import timedelta
from pathlib import Path
from typing import Optional, BinaryIO

from minio import Minio
from minio.error import S3Error
# fmt: off  MC80OmFIVnBZMlhtaVkzbGlaSHBsSXM2YWtnMVFRPT06Nzc1ZmZiOTE=

# Allow this standalone skill client to import the repository backend settings.
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

_SETTINGS_SPEC = importlib.util.spec_from_file_location(
    "_web_cli_minio_settings",
    BACKEND_ROOT / "app" / "config" / "settings.py",
)
if _SETTINGS_SPEC is None or _SETTINGS_SPEC.loader is None:
    raise ImportError("无法加载仓库 MinIO 配置")
_SETTINGS_MODULE = importlib.util.module_from_spec(_SETTINGS_SPEC)
_SETTINGS_SPEC.loader.exec_module(_SETTINGS_MODULE)
settings = _SETTINGS_MODULE.settings

logger = logging.getLogger(__name__)


def _mask_secret(value: Optional[str]) -> str:
    """脱敏输出密钥类配置，避免日志泄露完整凭据。"""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}***{value[-4:]}"


class MinIOError(Exception):
    """MinIO 操作错误的包装类，用于避免 S3Error 的 frozen 属性问题"""

    def __init__(self, message: str, code: Optional[str] = None, original_error: Optional[S3Error] = None):
        super().__init__(message)
        self.code = code
        self.original_error = original_error


class MinIOClient:
    """MinIO 客户端管理器"""

    bucket_name: str = settings.minio_bucket
    _client: Optional[Minio] = None
    _bucket_ensured: bool = False

    @classmethod
    def _log_request(cls, operation: str, **extra: object) -> None:
        """输出 MinIO 请求配置，密钥字段仅脱敏展示。"""
        logger.info(
            "MinIO %s request config: MINIO_ENDPOINT=%s, MINIO_BUCKET=%s, "
            "MINIO_SECURE=%s, MINIO_ACCESS_KEY=%s, MINIO_SECRET_KEY=%s, extra=%s",
            operation,
            settings.minio_endpoint,
            settings.minio_bucket,
            settings.minio_secure,
            _mask_secret(settings.minio_access_key),
            _mask_secret(settings.minio_secret_key),
            extra,
        )

    @classmethod
    def get_client(cls) -> Minio:
        """获取 MinIO 客户端实例"""
        if cls._client is None:
            cls._log_request("initialize_client")
            cls._client = Minio(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
                region=settings.minio_region,
            )
        return cls._client

    @classmethod
    def test_connection(cls) -> dict[str, object]:
        """
        测试 MinIO 连接与目标桶访问状态。

        Returns:
            dict: 连接测试结果，不包含 access_key/secret_key 等敏感信息。
        """
        result: dict[str, object] = {
            "success": False,
            "endpoint": settings.minio_endpoint,
            "bucket": settings.minio_bucket,
            "secure": settings.minio_secure,
            "bucket_exists": False,
        }

        try:
            cls._log_request("test_connection")
            client = cls.get_client()
            bucket_exists = client.bucket_exists(settings.minio_bucket)
            result.update({
                "success": True,
                "bucket_exists": bucket_exists,
            })
        except S3Error as e:
            result.update({
                "error": e.message,
                "code": e.code,
            })
        except Exception as e:
            result["error"] = str(e)

        return result

    @classmethod
    def ensure_bucket(cls) -> None:
        """确保存储桶存在"""
        if cls._bucket_ensured:
            return

        cls._log_request("ensure_bucket")
        client = cls.get_client()
        bucket_name = settings.minio_bucket
# noqa  MS80OmFIVnBZMlhtaVkzbGlaSHBsSXM2YWtnMVFRPT06Nzc1ZmZiOTE=

        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
        except S3Error as e:
            # 桶已存在，忽略错误
            if e.code != "BucketAlreadyOwnedByYou":
                raise MinIOError(
                    f"Failed to ensure bucket exists: {e.message}",
                    code=e.code,
                    original_error=e
                )

        cls._bucket_ensured = True

    @classmethod
    def upload_file(
        cls,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传文件到 MinIO

        Args:
            object_name: 对象名称（存储路径）
            data: 文件数据流
            length: 文件长度
            content_type: 内容类型

        Returns:
            str: 对象名称
        """
        try:
            cls._log_request(
                "upload_file",
                object_name=object_name,
                length=length,
                content_type=content_type,
            )
            cls.ensure_bucket()
            client = cls.get_client()
# noqa  Mi80OmFIVnBZMlhtaVkzbGlaSHBsSXM2YWtnMVFRPT06Nzc1ZmZiOTE=

            client.put_object(
                bucket_name=settings.minio_bucket,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type,
            )

            return object_name
        except S3Error as e:
            raise MinIOError(
                f"Failed to upload file '{object_name}': {e.message}",
                code=e.code,
                original_error=e
            )

    @classmethod
    def upload_bytes(
        cls,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传字节数据到 MinIO

        Args:
            object_name: 对象名称
            data: 字节数据
            content_type: 内容类型

        Returns:
            str: 对象名称
        """
        return cls.upload_file(
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    @classmethod
    def download_file(cls, object_name: str) -> bytes:
        """
        从 MinIO 下载文件

        Args:
            object_name: 对象名称

        Returns:
            bytes: 文件内容
        """
        try:
            cls._log_request("download_file", object_name=object_name)
            client = cls.get_client()

            response = client.get_object(
                bucket_name=settings.minio_bucket,
                object_name=object_name,
            )

            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            raise MinIOError(
                f"Failed to download file '{object_name}': {e.message}",
                code=e.code,
                original_error=e
            )

    @classmethod
    def get_presigned_url(
        cls,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        获取预签名 URL（用于下载）

        Args:
            object_name: 对象名称
            expires: 过期时间

        Returns:
            str: 预签名 URL
        """
        try:
            cls._log_request(
                "get_presigned_url",
                object_name=object_name,
                expires_seconds=int(expires.total_seconds()),
            )
            client = cls.get_client()

            return client.presigned_get_object(
                bucket_name=settings.minio_bucket,
                object_name=object_name,
                expires=expires,
            )
        except S3Error as e:
            raise MinIOError(
                f"Failed to get presigned URL for '{object_name}': {e.message}",
                code=e.code,
                original_error=e
            )

    @classmethod
    def delete_file(cls, object_name: str) -> None:
        """
        从 MinIO 删除文件

        Args:
            object_name: 对象名称
        """
        try:
            cls._log_request("delete_file", object_name=object_name)
            client = cls.get_client()

            client.remove_object(
                bucket_name=settings.minio_bucket,
                object_name=object_name,
            )
        except S3Error as e:
            raise MinIOError(
                f"Failed to delete file '{object_name}': {e.message}",
                code=e.code,
                original_error=e
            )

    @classmethod
    def file_exists(cls, object_name: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_name: 对象名称

        Returns:
            bool: 是否存在
        """
        try:
            cls._log_request("file_exists", object_name=object_name)
            client = cls.get_client()
# fmt: off  My80OmFIVnBZMlhtaVkzbGlaSHBsSXM2YWtnMVFRPT06Nzc1ZmZiOTE=

            client.stat_object(
                bucket_name=settings.minio_bucket,
                object_name=object_name,
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise MinIOError(
                f"Failed to check if file '{object_name}' exists: {e.message}",
                code=e.code,
                original_error=e
            )


def main() -> int:
    """命令行调试入口：测试 MinIO 是否连接正常。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    try:
        result = MinIOClient.test_connection()
    except Exception:
        logger.error("MinIO connection test failed")
        result = {"success": False}
    safe_result = {
        key: value
        for key, value in result.items()
        if not any(
            sensitive in key.lower()
            for sensitive in ("access_key", "secret_key", "password", "token")
        )
        and key != "error"
    }
    if not result.get("success"):
        safe_result["error"] = "MinIO connection failed"
    print(json.dumps(safe_result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
