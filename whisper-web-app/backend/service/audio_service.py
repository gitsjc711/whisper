import os
import random
from ..utils.file_utils import check_ffmpeg


class AudioService:
    """音频处理服务"""

    @staticmethod
    def add_noise(file_path, noise_db=-10):
        """
        给音频添加噪声
        :param file_path: 音频文件路径
        :param noise_db: 噪声强度 (dB)，范围 -20 到 -5，值越大噪声越强
        :return: 加噪后的音频文件路径
        """
        try:
            from pydub import AudioSegment
            import numpy as np

            if not check_ffmpeg():
                print("由于缺少ffmpeg，跳过加噪处理")
                return file_path

            print(f"开始加噪处理: {noise_db}dB")
            audio = AudioSegment.from_file(file_path)

            # 生成与音频相同长度的白噪声
            duration_ms = len(audio)
            sample_rate = audio.frame_rate
            num_samples = int(duration_ms * sample_rate / 1000)

            # 生成高斯白噪声
            noise_array = np.random.normal(0, 1, num_samples)

            # 将噪声转换为 AudioSegment
            # 先归一化噪声
            noise_array = noise_array / np.max(np.abs(noise_array))

            # 计算噪声强度（相对于音频）
            audio_db = audio.dBFS
            target_noise_db = audio_db + noise_db

            # 将 dB 转换为线性比例
            noise_ratio = 10 ** (target_noise_db / 20.0)

            # 应用噪声强度
            noise_array = noise_array * noise_ratio

            # 创建噪声 AudioSegment
            noise_audio = AudioSegment(
                noise_array.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,
                channels=1
            )

            # 混合音频和噪声
            noisy_audio = audio.overlay(noise_audio)

            # 保存加噪后的音频到专门的目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            noisy_folder = os.path.join(base_dir, 'noisy_audio')
            os.makedirs(noisy_folder, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            noisy_filename = f"{base_name}_noisy_{abs(int(noise_db))}dB.wav"
            noisy_path = os.path.join(noisy_folder, noisy_filename)
            
            noisy_audio.export(noisy_path, format="wav")

            print(f"加噪完成: {noisy_path}")
            return noisy_path

        except Exception as e:
            print(f"加噪失败: {e}")
            import traceback
            traceback.print_exc()
            return file_path

    @staticmethod
    def normalize_audio_format(file_path):
        """将音频转换为标准WAV格式"""
        try:
            from pydub import AudioSegment

            if not check_ffmpeg():
                print("由于缺少ffmpeg，跳过音频标准化")
                return file_path

            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)

            base, ext = os.path.splitext(file_path)
            normalized_path = f"{base}_normalized.wav"
            audio.export(normalized_path, format="wav")

            if os.path.exists(normalized_path) and normalized_path != file_path:
                try:
                    os.remove(file_path)
                    print(f"已删除原文件: {file_path}")
                except Exception as e:
                    print(f"删除原文件失败: {e}")

            print(f"音频标准化成功: {normalized_path}")
            return normalized_path

        except FileNotFoundError as e:
            print(f"音频标准化失败 - 找不到ffmpeg: {e}")
            return file_path
        except Exception as e:
            print(f"音频标准化失败: {e}")
            return file_path

    @staticmethod
    def save_audio_file(file, upload_folder, allowed_extensions, noise_level=None):
        """
        保存上传的音频文件，可选加噪
        :param file: 上传的文件对象
        :param upload_folder: 上传文件夹路径
        :param allowed_extensions: 允许的文件扩展名
        :param noise_level: 噪声强度 (dB)，None 表示不加噪
        :return: (文件路径, 文件名)
        """
        from backend.utils.file_utils import allowed_file, generate_filename

        if file and allowed_file(file.filename, allowed_extensions):
            filename = generate_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # 先标准化
            normalized_path = AudioService.normalize_audio_format(file_path)

            # 如果需要加噪
            if noise_level is not None:
                noisy_path = AudioService.add_noise(normalized_path, float(noise_level))
                return noisy_path, os.path.basename(noisy_path)

            return normalized_path, os.path.basename(normalized_path)
        return None, None