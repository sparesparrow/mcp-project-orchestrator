#!/usr/bin/env python3
"""Extract selected members from a remote ZIP over HTTP Range requests (no full download).

Usage: remote_zip_extract.py URL OUTDIR member [member ...]
Prints the member list with `--list`: remote_zip_extract.py URL --list
"""
import io
import sys
import urllib.request
import zipfile


class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
            if r.headers.get("Accept-Ranges", "").lower() != "bytes":
                raise SystemExit("server does not advertise Accept-Ranges: bytes")
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        if whence == 0:
            self.pos = off
        elif whence == 1:
            self.pos += off
        else:
            self.pos = self.size + off
        return self.pos

    def read(self, n=-1):
        if n < 0 or self.pos + n > self.size:
            n = self.size - self.pos
        if n <= 0:
            return b""
        end = self.pos + n - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        self.pos += len(data)
        return data

    def readinto(self, b):
        d = self.read(len(b))
        b[: len(d)] = d
        return len(d)


def main():
    url = sys.argv[1]
    f = RangeFile(url)
    z = zipfile.ZipFile(io.BufferedReader(f, buffer_size=1 << 20))
    if sys.argv[2] == "--list":
        for i in z.infolist():
            print(i.file_size, i.compress_size, i.filename)
        return
    out = sys.argv[2]
    for m in sys.argv[3:]:
        z.extract(m, out)
        print("extracted", m)


if __name__ == "__main__":
    main()
