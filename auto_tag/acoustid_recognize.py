"""
测试 Acoustid 音乐识别服务
Acoustid 是一个开源的音乐识别服务，基于 Chromaprint 音频指纹算法
"""
import asyncio
import subprocess
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Acoustid API Key（免费额度：100 次/天）
ACOUSTID_API_KEY = "cSpUJKpD"  # 这是一个公开的测试 key

# Acoustid 查找接口
ACOUSTID_LOOKUP_URL = "https://api.acoustid.org/v2/lookup"


def get_chromaprint_fingerprint(file_path: str) -> tuple:
    """
    使用 ffmpeg 的 chromaprint 滤镜生成音频指纹

    Args:
        file_path: 音频文件路径

    Returns:
        tuple: (duration, fingerprint)
    """
    # 使用 ffmpeg 的 chromaprint 滤镜
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-f", "chromaprint",
        "-fp_format", "1",  # base64 格式
        "-"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        output = result.stdout.decode('utf-8').strip()
        # 输出格式：Chromaprint,1,<duration>,<fingerprint>
        parts = output.split(',')
        if len(parts) >= 4:
            duration = int(parts[2])
            fingerprint = parts[3]
            logger.info(f"[Acoustid] 生成指纹成功: duration={duration}s, fp_len={len(fingerprint)}")
            return duration, fingerprint
        else:
            logger.error(f"[Acoustid] 指纹格式错误: {output}")
            return None, None
    except subprocess.CalledProcessError as e:
        logger.error(f"[Acoustid] ffmpeg 执行失败: {e.stderr.decode('utf-8', errors='ignore')}")
        raise
    except Exception as e:
        logger.error(f"[Acoustid] 生成指纹失败: {e}")
        raise


async def lookup_with_acoustid(file_path: str) -> dict | None:
    """
    使用 Acoustid 服务识别歌曲

    Args:
        file_path: 音频文件路径

    Returns:
        dict | None: 识别结果
    """
    import aiohttp

    try:
        # 1. 生成音频指纹
        duration, fingerprint = get_chromaprint_fingerprint(file_path)
        if not fingerprint:
            logger.warning("[Acoustid] 无法生成音频指纹")
            return None

        # 2. 调用 Acoustid 查找接口
        params = {
            "client": ACOUSTID_API_KEY,
            "fingerprint": fingerprint,
            "duration": duration,
            "meta": "recordings releasegroups",  # 获取更多信息
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                ACOUSTID_LOOKUP_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"[Acoustid] 接口返回: {data}")

                    if data.get("status") == "ok" and data.get("results"):
                        result = data["results"][0]
                        recordings = result.get("recordings", [])
                        if recordings:
                            recording = recordings[0]
                            # 获取专辑信息
                            releasegroups = result.get("releasegroups", [])
                            album_name = ""
                            if releasegroups:
                                album_name = releasegroups[0].get("title", "")

                            return {
                                "title": recording.get("title", ""),
                                "artist": recording.get("artists", [{}])[0].get("name", ""),
                                "album": album_name,
                                "duration": recording.get("duration", 0) / 1000,
                                "acoustid_id": result.get("id", ""),
                                "musicbrainz_id": recording.get("id", ""),
                            }

                    logger.warning("[Acoustid] 未找到匹配结果")
                    return None

                logger.warning(f"[Acoustid] 请求失败: status={response.status}")
                return None

    except Exception as e:
        logger.error(f"[Acoustid] 识别失败: {e}", exc_info=True)
        return None


async def test_recognize(file_path: str):
    """测试函数"""
    print(f"[*] 测试文件: {file_path}")
    print(f"[*] 文件大小: {Path(file_path).stat().st_size / 1024 / 1024:.2f} MB")
    print()

    result = await lookup_with_acoustid(file_path)

    print("\n" + "=" * 60)
    print("[*] 识别结果:")
    print("=" * 60)

    if result:
        print("[OK] 识别成功!")
        print(f"   歌曲: {result.get('title', 'N/A')}")
        print(f"   艺术家: {result.get('artist', 'N/A')}")
        print(f"   专辑: {result.get('album', 'N/A')}")
        print(f"   时长: {result.get('duration', 'N/A')}s")
        print(f"   Acoustid ID: {result.get('acoustid_id', 'N/A')}")
    else:
        print("[!] 识别失败，未找到匹配结果")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = r"c:\Users\Administrator\Desktop\MyProgram\Imusic\tests\fixtures\song\32671414_da3-1-30216.mp3"

    asyncio.run(test_recognize(test_file))
