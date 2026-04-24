# -*- coding: utf-8 -*-
"""
GUI 工作线程模块

该模块提供用于后台任务处理的工作线程类。

@module workers
@author Backend Architect
@version 1.0.0
"""

from auto_tag.gui.workers.recognize_worker import RecognizeWorker
from auto_tag.gui.workers.lyric_worker import LyricWorker, LyricEmbedWorker
from auto_tag.gui.workers.song_search_worker import SongSearchWorker

__all__ = ["RecognizeWorker", "LyricWorker", "LyricEmbedWorker", "SongSearchWorker"]
