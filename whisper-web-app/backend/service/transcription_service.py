import os
from ..model.whisper_model import WhisperModelManager


class TranscriptionService:
    """语音转录服务"""

    @staticmethod
    def transcribe_audio(audio_path):
        """使用Whisper转录音频"""
        try:
            if not os.path.isabs(audio_path):
                audio_path = os.path.abspath(audio_path)

            if not os.path.exists(audio_path):
                print(f"文件不存在: {audio_path}")
                return None

            print(f"开始转录文件: {audio_path}")
            model = WhisperModelManager.get_model()
            result = model.transcribe(audio_path)

            return {
                'text': result['text'],
                'language': result.get('language', 'unknown'),
                'duration': result.get('duration', 0),
                'segments': [
                    {
                        'start': s['start'],
                        'end': s['end'],
                        'text': s['text']
                    } for s in result.get('segments', [])
                ]
            }
        except Exception as e:
            print(f"转录失败: {e}")
            import traceback
            traceback.print_exc()
            return None