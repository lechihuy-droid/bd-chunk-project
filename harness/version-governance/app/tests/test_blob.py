from adapters.minio_blob import MinioBlobAdapter


class Client:
    class exceptions:
        class ClientError(Exception):
            pass

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.puts = 0

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")

    def put_object(self, Bucket, Key, Body, ContentType):
        self.puts += 1
        self.objects[Key] = (Body, ContentType)


def test_put_immutable_is_content_addressed_and_idempotent() -> None:
    adapter = MinioBlobAdapter("http://minio", "key", "secret")
    client = Client()
    adapter.client = client
    key = "project/API_BASIC_DESIGN/F001/" + "a" * 64 + ".md"
    first = adapter.put_immutable(key=key, data=b"# BD\n", mime_type="text/markdown")
    second = adapter.put_immutable(key=key, data=b"# BD\n", mime_type="text/markdown")
    assert client.puts == 1
    assert first == second
    assert first.uri == f"s3://vgov-artifacts/{key}"
