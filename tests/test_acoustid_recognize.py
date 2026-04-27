import asyncio
import os
import sys
import json
import subprocess
import tempfile
from urllib.parse import urlencode

import aiohttp

ACOUSTID_API_KEY = "cSpUJKpD"
ACOUSTID_LOOKUP_URL = "https://api.acoustid.org/v2/lookup"

TEST_FILES = [
    r"f:\Code\Imusic\tests\fixtures\song\32671406_da3-1-30232.mp3",
    r"f:\Code\Imusic\tests\fixtures\song\32671407_da3-1-30232.mp3",
    r"f:\Code\Imusic\tests\fixtures\song\32671414_da3-1-30232.mp3",
    r"f:\Code\Imusic\tests\fixtures\song\32671415_da3-1-30232.mp3",
    r"f:\Code\Imusic\tests\fixtures\song\32671427_da3-1-30232.mp3",
]


def generate_fingerprint(file_path: str) -> tuple[str | None, int]:
    """
    Generate Chromaprint fingerprint using ffmpeg DEFAULT format.
    
    The default chromaprint output (no -fp_format flag) produces
    a base64-encoded compressed fingerprint that Acoustid API accepts.
    
    Returns:
        (fingerprint_string, duration_seconds) or (None, 0)
    """
    fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)

    try:
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json", "-show_format",
            file_path
        ]
        probe_result = subprocess.run(
            probe_cmd, capture_output=True, timeout=10, check=True
        )
        probe_data = json.loads(probe_result.stdout.decode("utf-8"))
        duration = int(float(probe_data.get("format", {}).get("duration", 0)))

        # Use DEFAULT chromaprint format (no -fp_format)
        # This produces the compressed base64 fingerprint that Acoustid expects
        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-f", "chromaprint",
            tmp_path
        ]
        result = subprocess.run(
            cmd, capture_output=True, timeout=120, check=True
        )

        with open(tmp_path, "r", encoding="ascii") as f:
            fingerprint = f.read().strip()

        if not fingerprint or len(fingerprint) < 10:
            return None, duration

        return fingerprint, duration

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="replace")[-300:] if e.stderr else ""
        print(f"    [FFmpeg Error] exit={e.returncode}: {stderr}")
        return None, 0
    except Exception as e:
        print(f"    [Error] {e}")
        return None, 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def lookup_acoustid(fingerprint: str, duration: int) -> dict | None:
    body = urlencode({
        "client": ACOUSTID_API_KEY,
        "fingerprint": fingerprint,
        "duration": str(duration),
        "meta": "recordings releasegroups",
    })

    async with aiohttp.ClientSession() as session:
        async with session.post(
            ACOUSTID_LOOKUP_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"    [API] HTTP {response.status}: {text[:200]}")
                return None
            return await response.json()


async def main():
    print("=" * 70)
    print("Acoustid Audio Fingerprint Recognition Test")
    print("(Chromaprint default format + Acoustid API)")
    print("=" * 70)

    for i, file_path in enumerate(TEST_FILES, 1):
        filename = os.path.basename(file_path)
        print(f"\n[{i}/5] File: {filename}")
        print("-" * 50)

        if not os.path.exists(file_path):
            print(f"  [FAIL] File not found!")
            continue

        print(f"  Generating fingerprint (default format)...")
        fingerprint, duration = generate_fingerprint(file_path)

        if not fingerprint:
            print(f"  [FAIL] Failed to generate fingerprint")
            continue

        print(f"  Duration: {duration}s, FP: {len(fingerprint)} chars")
        print(f"  FP preview: {fingerprint[:60]}...")

        print(f"  Querying Acoustid...")
        result = await lookup_acoustid(fingerprint, duration)

        if result and result.get("status") == "ok" and result.get("results"):
            top = result["results"][0]
            recordings = top.get("recordings", [])
            if recordings:
                rec = recordings[0]
                title = rec.get("title", "Unknown")
                artists = rec.get("artists", [])
                artist = artists[0]["name"] if artists else "Unknown"
                rgs = top.get("releasegroups", [])
                album = rgs[0]["title"] if rgs else "Unknown"
                score = top.get("score", 0)
                aid = top.get("id", "")

                print(f"  [OK] Matched! (score={score}, id={aid})")
                print(f"       Title:  {title}")
                print(f"       Artist: {artist}")
                print(f"       Album:  {album}")
            else:
                print(f"  [PARTIAL] Results but no recording info")
                print(f"         {json.dumps(top)[:300]}")
        else:
            msg = "No matches in database"
            if result and "error" in result:
                msg = f'API Error: {result["error"].get("message", "?")}'
            elif result:
                msg = f'status={result.get("status")}'
            print(f"  [FAIL] {msg}")

    print("\n" + "=" * 70)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
