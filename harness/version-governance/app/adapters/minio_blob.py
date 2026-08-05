import hashlib
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from ports.blob_store import BlobRef


class MinioBlobAdapter:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str = "vgov-artifacts") -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put_immutable(self, *, key: str, data: bytes, mime_type: str) -> BlobRef:
        digest = hashlib.sha256(data).hexdigest()
        if not self.exists(key):
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=mime_type)
        return BlobRef(f"s3://{self.bucket}/{key}", f"sha256:{digest}", len(data), mime_type)

    def get(self, uri: str) -> bytes:
        parsed = urlparse(uri)
        if parsed.scheme != "s3" or parsed.netloc != self.bucket or not parsed.path.lstrip("/"):
            raise ValueError(f"Unsupported blob URI: {uri}")
        return self.client.get_object(Bucket=self.bucket, Key=parsed.path.lstrip("/"))["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"].get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
