"""Verify Gradle's signed outputs with the installed Android build tools."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def signer_fingerprints(build_tools, apk):
    report = subprocess.check_output(
        [build_tools / "apksigner", "verify", "--print-certs-pem", apk], text=True
    )
    certificates = re.findall(
        r"-----BEGIN CERTIFICATE-----\s*(.*?)\s*-----END CERTIFICATE-----", report, re.DOTALL
    )
    return {hashlib.sha256(base64.b64decode("".join(c.split()), validate=True)).hexdigest()
            for c in certificates}


def verify():
    output = Path("source/app/build/outputs/apk/meta/release")
    metadata = json.loads((output / "output-metadata.json").read_text())
    app = "com.github.vertno.clash.meta"
    if metadata["applicationId"] != app:
        raise ValueError("Unexpected application ID")
    expected_signer = Path("control/release/certificate.sha256").read_text().strip().lower()
    versions = (Path(os.environ["ANDROID_HOME"]) / "build-tools").iterdir()
    tools = max((p for p in versions if re.fullmatch(r"\d+\.\d+\.\d+", p.name)),
                key=lambda p: tuple(map(int, p.name.split("."))))
    for row in metadata["elements"]:
        apk = output / row["outputFile"]
        if signer_fingerprints(tools, apk) != {expected_signer}:
            raise ValueError(f"{apk.name} uses a different signing certificate")


if __name__ == "__main__":
    verify()
