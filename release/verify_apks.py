"""Verify Gradle's signed outputs with the installed Android build tools."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile


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
    version_name = os.environ["VERSION_NAME"]
    version_code = int(os.environ["VERSION_CODE"])
    versions = (Path(os.environ["ANDROID_HOME"]) / "build-tools").iterdir()
    tools = max((p for p in versions if re.fullmatch(r"\d+\.\d+\.\d+", p.name)),
                key=lambda p: tuple(map(int, p.name.split("."))))
    abis = set()
    for row in metadata["elements"]:
        apk = output / row["outputFile"]
        if row["versionCode"] != version_code or not row["versionName"].startswith(version_name + "."):
            raise ValueError("Gradle version mismatch")
        signers = signer_fingerprints(tools, apk)
        if signers != {expected_signer}:
            raise ValueError(f"{apk.name}: expected public certificate {expected_signer}, found {sorted(signers)}")
        manifest = subprocess.check_output([tools / "aapt", "dump", "xmltree", apk, "AndroidManifest.xml"], text=True)
        if any(app + ".action." + a not in manifest for a in ("START_CLASH", "STOP_CLASH", "TOGGLE_CLASH")):
            raise ValueError("External actions have the wrong app ID")
        with zipfile.ZipFile(apk) as archive:
            def native_abis(filename):
                return {n.split("/")[1] for n in archive.namelist() if n.startswith("lib/") and n.endswith("/" + filename)}
            go = native_abis("libclash.so")
            declared = {f["value"] for f in row["filters"] if f["filterType"] == "ABI"}
            if not go or go != native_abis("libbridge.so") or (declared and go != declared):
                raise ValueError("Incomplete native ABI libraries")
            abis.update(go)
        print(apk.name, version_code, expected_signer)
    if "arm64-v8a" not in abis:
        raise ValueError("Missing phone ABI")


if __name__ == "__main__":
    verify()
