from ftplib import error_perm
import os
from urllib.parse import urlparse
from pystac import Link
from pystac.stac_io import DefaultStacIO
from typing import Union, Any
import zipfile
import logging
from subprocess import Popen, PIPE, STDOUT
import boto3
# from botocore.errorfactory import ClientError
import glob

logger = logging.getLogger(__name__)


class CustomStacIO(DefaultStacIO):
    def __init__(self):
        self.s3 = boto3.resource("s3")

    def read_text(self, source: Union[str, Link], *args: Any,
                  **kwargs: Any) -> str:
        parsed = urlparse(source)
        if parsed.scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path[1:]

            obj = self.s3.Object(bucket, key)
            return obj.get()["Body"].read().decode("utf-8")
        else:
            return super().read_text(source, *args, **kwargs)

    def write_text(self, dest: Union[str, Link], txt: str, *args: Any,
                   **kwargs: Any) -> None:
        parsed = urlparse(dest)
        if parsed.scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path[1:]
            s3 = boto3.resource("s3")
            s3.Object(bucket, key).put(Body=txt, ContentEncoding="utf-8")
        else:
            super().write_text(dest, txt, *args, **kwargs)


def call(command):
    def log_subprocess_output(pipe):
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            logger.info(line.decode("utf-8").strip('\n'))

    process = Popen(command, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        log_subprocess_output(process.stdout)
    return process.wait()  # 0 means success


def upload_to_s3(parsed, local_path):
    bucket = parsed.netloc
    key = parsed.path[1:]
    s3 = boto3.resource("s3")
    print(f"Uploading {os.path.basename(local_path)}")
    s3.Bucket(bucket).upload_file(local_path, key)


def get_existing_paths(directory, ending):
    parsed = urlparse(directory)

    if parsed.scheme == "s3":
        bucket = parsed.netloc
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket)
        paths = []
        for i, page in enumerate(pages):
            print(f"S3 page {i+1}/?")
            paths += [
                f"{directory}/{d['Key']}" for d in page['Contents']
                if d['Key'][-len(ending):] == ending
            ]
        return paths

    else:
        return glob.glob(f"{directory}{os.sep}**{os.sep}*{ending}",
                         recursive=True)


# def file_exists(path, paths_s3):
#     parsed = urlparse(path)

#     if parsed.scheme == "s3":
#         bucket = parsed.netloc
#         key = parsed.path[1:]
#         s3 = boto3.client('s3')
#         try:
#             s3.head_object(Bucket=bucket, Key=key)
#             return True
#         except ClientError:
#             # Not found
#             return False

#     else:
#         return os.path.exists(path)


def download_from_ftp(href, out_path, ftp):
    path = href.split(ftp.ftp_site)[-1]
    print(f"Downloading {os.path.basename(path)}")
    with open(out_path, 'wb') as f:
        try:
            ftp.ftp.retrbinary(f"RETR {path}", f.write)
            return True
        except error_perm:
            print(f"Failed to open {path} on FTP")
            return False


def unzip(zip_path, out_folder):
    zfile = zipfile.ZipFile(zip_path, 'r')
    out_paths = []

    for zip_file in [f for f in zfile.namelist() if '.tif' in f]:
        (folder, filename) = os.path.split(zip_file)
        out_path = os.path.join(out_folder, filename)
        out_paths.append(out_path)

        print(f"Decompressing {folder}{filename}")
        with open(out_path, 'wb') as f:
            f.write(zfile.read(zip_file))

    return out_paths


def bbox(f):
    x, y = zip(*list(explode(f["geometry"]["coordinates"])))
    return min(x), min(y), max(x), max(y)


def transform_geom(transformer, geom):
    """
    Transform the geometry of a given feature
    Allow multipolygons
    """
    new_coords = []
    for ring in geom:
        x2, y2 = transformer.transform(*zip(*ring))
        new_coords.append(list(zip(y2, x2)))

    return new_coords


def explode(coords):
    # from https://gis.stackexchange.com/questions/90553/fiona-get-each-feature-extent-bounds
    """Explode a GeoJSON geometry's coordinates object and yield coordinate tuples.
    As long as the input is conforming, the type of the geometry doesn't matter."""
    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f
