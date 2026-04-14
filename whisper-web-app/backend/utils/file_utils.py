import os
import math
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return '0 Bytes'
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB']
    i = int(math.floor(math.log(size_bytes) / math.log(k)))
    return f"{round(size_bytes / (k ** i), 2)} {sizes[i]}"


def generate_filename(original_filename):
    """生成带时间戳的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = secure_filename(original_filename)
    name, ext = os.path.splitext(original_name)
    return f"{name}_{timestamp}{ext}"


def check_ffmpeg():
    """检查ffmpeg是否可用"""
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        print("警告: 未找到ffmpeg，请安装ffmpeg并添加到PATH环境变量")
        print("可以通过以下方式安装:")
        print("1. conda install -c conda-forge ffmpeg")
        print("2. 从 https://ffmpeg.org/download.html 下载并添加到PATH")
        return False
    print(f"找到ffmpeg: {ffmpeg_path}")
    return True