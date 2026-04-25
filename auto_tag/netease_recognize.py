"""
网易云音乐听歌识曲实现
基于 ffmpeg 提取音频特征并调用网易云 /audio/match 接口
"""
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# 网易云听歌识曲接口
NETEASE_AUDIO_MATCH_URL = "https://interface.music.163.com/weapi/song/recognition"


def extract_audio_segment(file_path: str, duration: int = 10) -> str:
    """
    从音频文件中提取一段音频用于识别

    Args:
        file_path: 音频文件路径
        duration: 提取时长（秒）

    Returns:
        str: 临时音频文件路径
    """
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # 使用 ffmpeg 提取音频片段
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-t", str(duration),  # 提取前 duration 秒
        "-ar", "44100",       # 标准采样率
        "-ac", "2",           # 立体声
        "-y",                 # 覆盖输出文件
        temp_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            check=True
        )
        logger.info(f"[NetEaseExtract] 提取音频片段成功: {temp_path}")
        return temp_path
    except subprocess.CalledProcessError as e:
        logger.error(f"[NetEaseExtract] ffmpeg 执行失败: {e.stderr.decode('utf-8', errors='ignore')}")
        raise
    except Exception as e:
        logger.error(f"[NetEaseExtract] 提取音频失败: {e}")
        raise


async def recognize_with_netease(file_path: str) -> dict | None:
    """
    使用网易云音乐听歌识曲接口识别歌曲

    Args:
        file_path: 音频文件路径

    Returns:
        dict | None: 识别结果，包含歌曲信息；识别失败返回 None
    """
    import aiohttp
    import json

    try:
        # 1. 提取音频片段
        temp_path = extract_audio_segment(file_path, duration=10)

        # 2. 读取音频数据并转换为 base64
        with open(temp_path, 'rb') as f:
            audio_data = f.read()

        import base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        logger.info(f"[NetEaseRecognize] 准备调用网易云听歌识曲: {file_path}")
        logger.info(f"[NetEaseRecognize] 音频数据大小: {len(audio_data)} 字节")

        # 3. 调用网易云听歌识曲接口
        # 注意：网易云的接口需要特殊的参数加密，这里尝试直接调用
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://music.163.com/",
            "Origin": "https://music.163.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # 尝试使用不同的接口
        # 接口 1: /weapi/song/recognition
        params = {
            "audioFP": audio_base64[:100],  # 只发送部分数据测试
            "duration": 10,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                NETEASE_AUDIO_MATCH_URL,
                data=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"[NetEaseHTTP] 接口返回: {json.dumps(data, ensure_ascii=False)[:500]}")

                    if data.get("code") == 200:
                        # 解析返回结果
                        result_data = data.get("data", {})
                        matches = result_data.get("matches", [])
                        if matches:
                            match = matches[0]
                            song = match.get("song", {})
                            return {
                                "title": song.get("name", ""),
                                "artist": song.get("artists", [{}])[0].get("name", ""),
                                "album": song.get("album", {}).get("name", ""),
                                "cover": song.get("album", {}).get("picUrl", ""),
                                "duration": song.get("duration", 0) // 1000,
                                "song_id": song.get("id", 0),
                            }

                logger.warning(f"[NetEaseHTTP] 识别失败: status={response.status}")
                return None

    except Exception as e:
        logger.error(f"[NetEaseRecognize] 识别失败: {e}", exc_info=True)
        return None
    finally:
        # 清理临时文件
        if 'temp_path' in locals() and Path(temp_path).exists():
            Path(temp_path).unlink()


async def test_recognize(file_path: str):
    """测试函数"""
    print(f"[*] 测试文件: {file_path}")
    print(f"[*] 文件大小: {Path(file_path).stat().st_size / 1024 / 1024:.2f} MB")
    print()

    result = await recognize_with_netease(file_path)

    print("\n" + "=" * 60)
    print("[*] 识别结果:")
    print("=" * 60)

    if result:
        print("[OK] 识别成功!")
        print(f"   歌曲: {result.get('title', 'N/A')}")
        print(f"   艺术家: {result.get('artist', 'N/A')}")
        print(f"   专辑: {result.get('album', 'N/A')}")
        print(f"   时长: {result.get('duration', 'N/A')}s")
        print(f"   歌曲ID: {result.get('song_id', 'N/A')}")
    else:
        print("[!] 识别失败，未找到匹配结果")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = r"c:\Users\Administrator\Desktop\MyProgram\Imusic\tests\fixtures\song\32671414_da3-1-30216.mp3"

    asyncio.run(test_recognize(test_file))
