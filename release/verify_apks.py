import json,os,re,subprocess,zipfile
from pathlib import Path
source=Path("source")
out=source/"app/build/outputs/apk/meta/release"
meta=json.loads((out/"output-metadata.json").read_text())
app="com.github.vertno.clash.meta"
if meta["applicationId"]!=app: raise ValueError("Unexpected application ID")
fp=Path("control/release/certificate.sha256").read_text().strip()
version=os.environ["VERSION_NAME"]
expected=int(os.environ["VERSION_CODE"])
tools=max((p for p in (Path(os.environ["ANDROID_HOME"])/"build-tools").iterdir() if re.fullmatch(r"\d+\.\d+\.\d+",p.name)),key=lambda p:tuple(map(int,p.name.split("."))))
abis=set()
for row in meta["elements"]:
    apk=out/row["outputFile"]
    if row["versionCode"]!=expected or not row["versionName"].startswith(version+"."): raise ValueError("Gradle version mismatch")
    cert=subprocess.check_output([tools/"apksigner","verify","--verbose","--print-certs",apk],text=True)
    if [s.lower() for s in re.findall(r"Signer #\d+ certificate SHA-256 digest: ([a-fA-F0-9]+)",cert)]!=[fp.lower()]: raise ValueError("Unexpected signing certificate")
    manifest=subprocess.check_output([tools/"aapt","dump","xmltree",apk,"AndroidManifest.xml"],text=True)
    if any(app+".action."+a not in manifest for a in ("START_CLASH","STOP_CLASH","TOGGLE_CLASH")): raise ValueError("External actions have the wrong app ID")
    with zipfile.ZipFile(apk) as z:
        go={p.split("/")[1] for p in z.namelist() if p.startswith("lib/") and p.endswith("/libclash.so")}
        bridge={p.split("/")[1] for p in z.namelist() if p.startswith("lib/") and p.endswith("/libbridge.so")}
        expected_abis={f["value"] for f in row["filters"] if f["filterType"]=="ABI"}
        if not go or go!=bridge or (expected_abis and go!=expected_abis): raise ValueError("Incomplete native ABI libraries")
        abis.update(go)
    print(apk.name, expected, fp)
if "arm64-v8a" not in abis: raise ValueError("Missing phone ABI")
