import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

from auto_tag.audio_recognize import recognize_and_rename_file
from shazamio import Shazam

TEST_FILE = r"f:\Code\Imusic\tests\fixtures\song\32671406_da3-1-30232.mp3"

shazam = Shazam()


async def main():
    print("=" * 70)
    print("Mimicking app worker flow for:", os.path.basename(TEST_FILE))
    print("=" * 70)

    result = await recognize_and_rename_file(
        file_path=TEST_FILE,
        shazam=shazam,
        modify=False,
        delay=10,
        nbr_retry=3,
        trace=True,  # Enable trace to see all engine attempts
        output_dir=None,
        plex_structure=False,
        copy_to=None,
        tag_only=False,
    )

    print("\n" + "=" * 70)
    print("RESULT:")
    print(f"  title:   {result.get('title')}")
    print(f"  author:  {result.get('author')}")
    print(f"  album:   {result.get('album')}")
    print(f"  source:  {result.get('source')}")
    print(f"  error:   {result.get('error')}")
    print(f"  results: {len(result.get('search_results', []))} items")
    if result.get("search_results"):
        for i, sr in enumerate(result["search_results"]):
            print(f"    [{i}] source={sr.get('source')} title={sr.get('title')} artist={sr.get('artist')}")


if __name__ == "__main__":
    asyncio.run(main())
