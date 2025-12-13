import io
import re
import typing as t
from urllib.parse import urlparse
import boto3
import requests
import zipstream
from flask import Blueprint, current_app, jsonify, request
from dotenv import load_dotenv

load_dotenv()

from utils.registry_utils import (
    load_registry,
    find_model_in_registry,
    add_to_audit,
)

download_bp = Blueprint("download", __name__)
BUCKET = "461-phase2-team12"
S3_CLIENT = boto3.client("s3", region_name="us-east-2")


from urllib.parse import urlparse

def extract_hf_repo_id(url: str) -> str | None:
    """
    Accepts:
    - https://huggingface.co/user/model
    - https://huggingface.co/model-name  (alias)
    """

    try:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        # Canonical case: owner/model
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"

        # Alias case: /model-name
        if len(parts) == 1 and parts[0]:
            # Assume official namespace
            return f"{parts[0].split('-')[0]}/{parts[0]}"

    except Exception:
        pass

    return None


def list_hf_files(repo_id: str) -> t.List[str]:
    """
    List files (siblings) in a HF model repo via HF API.
    """

    # build Hugging Face API endpoint
    api = f"https://huggingface.co/api/models/{repo_id}"

    # send API request
    r = requests.get(api, timeout=30)
    r.raise_for_status()

    # parse JSON response
    data = r.json()

    # extract siblings list
    siblings = data.get("siblings", [])

    # rfilename is the relative path in repo
    return [s.get("rfilename") for s in siblings if s.get("rfilename")]


def stream_hf_file(repo_id: str, filename: str, chunk_size: int = 512 * 1024):
    """
    Generator that yields bytes for a file in HF repo.
    Uses the 'resolve/main' raw file endpoint.
    """

    # build the raw-file URL
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"

    # send streaming request
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk


def filename_matches_component(
    filename: str, component: t.Optional[str]
) -> bool:
    """
    Simple heuristics for partitioning a HF repo into 'weights', 'tokenizer', 
    'dataset', 'configs', or 'full'.
    """

    if component in (None, "full"):
        return True

    lower = filename.lower()

    if component == "weights":
        # model weights / checkpoints often have these markers / extensions
        return bool(
            re.search(
                r"(pytorch_model|model_weights|\.bin$|\.pt$|\.safetensors$)",
                lower,
            )
        )

    if component == "tokenizer":
        return "tokenizer" in lower or "vocab" in lower or "merges" in lower

    if component == "dataset":
        return (
            "dataset" in lower
            or lower.startswith("data/")
            or "/data/" in lower
        )

    if component == "configs":
        return (
            "config" in lower
            or lower.endswith(".json")
            and ("config" in lower or "model" in lower)
        )

    # fallback: treat as full
    return True


class IteratorFileObj(io.RawIOBase):
    """
    Adapter: turn an iterator that yields bytes (chunks) into a file-like object
    with a .read(size) method so boto3.upload_fileobj can stream from it.

    The underlying iterator should yield bytes.
    """

    def __init__(self, iterator: t.Iterator[bytes]):
        self._it = iterator
        self._buf = bytearray()
        self._eof = False

    def readable(self):
        return True

    def readinto(self, b: bytearray) -> int:  # type: ignore[override]
        # readinto is preferred by boto3 for file-like objects
        if self._eof and not self._buf:
            return 0  # EOF

        # fill buffer until we have at least len(b) or EOF
        while len(self._buf) < len(b) and not self._eof:
            try:
                chunk = next(self._it)
            except StopIteration:
                self._eof = True
                break
            if chunk:
                self._buf.extend(chunk)

        # copy into b
        read_len = min(len(b), len(self._buf))
        if read_len == 0:
            return 0

        b[:read_len] = self._buf[:read_len]
        del self._buf[:read_len]
        return read_len

    # for compatibility, also provide read()
    def read(self, size: int = -1) -> bytes:
        if size == -1:
            # consume iterator fully
            chunks = [bytes(self._buf)]
            self._buf.clear()
            for c in self._it:
                chunks.append(c)
            self._eof = True
            return b"".join(chunks)
        else:
            out = bytearray()
            while len(out) < size and not self._eof:
                if self._buf:
                    take = min(size - len(out), len(self._buf))
                    out.extend(self._buf[:take])
                    del self._buf[:take]
                else:
                    try:
                        chunk = next(self._it)
                    except StopIteration:
                        self._eof = True
                        break
                    self._buf.extend(chunk)
            return bytes(out)


def stream_zip_of_hf_repo(
    repo_id: str, component: t.Optional[str] = None
) -> zipstream.ZipFile:
    """
    Build a zipstream.ZipFile where each file is added via write_iter using HF 
    file streaming.
    """

    z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)

    all_files = list_hf_files(repo_id)
    if not all_files:
        raise RuntimeError("No files found in HF repo")

    # add only files matching the requested component subset
    for filename in all_files:
        if not filename_matches_component(filename, component):
            continue

        # arcname should be the filename relative to repo root
        generator = stream_hf_file(repo_id, filename)
        z.write_iter(filename, generator)

    return z


def upload_zip_stream_to_s3(
    zip_stream: zipstream.ZipFile, s3_key: str
) -> None:
    """
    Upload a zipstream.ZipFile to S3 by wrapping the zip_stream's iterator into 
    a file-like object. This avoids writing the zip to disk.
    """

    # zip_stream is iterable: iter(zip_stream) yields chunks (bytes)
    iterator = iter(zip_stream)

    file_obj = IteratorFileObj(iterator)  # type: ignore

    # upload_fileobj will stream from file_obj
    S3_CLIENT.upload_fileobj(Fileobj=file_obj, Bucket=BUCKET, Key=s3_key)


def make_presigned_url(s3_key: str, expires_in: int = 7 * 24 * 3600) -> str:
    """
    Create a presigned GET URL for the uploaded object.
    Default expiry: 7 days.
    """

    return S3_CLIENT.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": s3_key},
        ExpiresIn=expires_in,
    )


@download_bp.route("/download/<model_id>", methods=["GET"])
def download_model(model_id):
    """
    Return a presigned URL for a previously packaged model.
    No re-download from HuggingFace since registration stage already handled it.
    """

    ENV = current_app.config.get("ENVIRONMENT", "local")

    # load registry
    if ENV == "local":
        registry_path = current_app.config["REGISTRY_PATH"]
        registry = load_registry(registry_path)
    else:
        registry = load_registry()

    # lookup model
    model = find_model_in_registry(registry, model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404

    # audit log
    name = "Name"  # TODO: replace with authenticated username
    admin = False  # TODO: replace accordingly
    artifact_name = model["metadata"].get("name", model_id)
    add_to_audit(name, admin, "model", model_id, artifact_name, "DOWNLOAD")

    # get S3 key stored during registration
    s3_key = model.get("data", {}).get("s3_key")
    if not s3_key:
        return jsonify({"error": "Model was never packaged or uploaded"}), 500

    # get URL expiration override
    expiry_seconds = int(request.args.get("expiry_seconds", 7 * 24 * 3600))

    # generate new presigned URL
    presigned_url = make_presigned_url(s3_key, expires_in=expiry_seconds)

    return jsonify(
        {
            "message": "Model found",
            "model_id": model_id,
            "artifact_name": artifact_name,
            "s3_key": s3_key,
            "url": presigned_url,
        }
    )
