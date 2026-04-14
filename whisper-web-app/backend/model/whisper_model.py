import whisper


class WhisperModelManager:
    """Whisper模型管理器（单例模式）"""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_model(cls, model_name="base"):
        """获取或加载Whisper模型"""
        if cls._model is None:
            print(f"正在加载Whisper {model_name}模型...")
            cls._model = whisper.load_model(model_name)
            print("模型加载完成！")
        return cls._model
    
    @classmethod
    def is_loaded(cls):
        """检查模型是否已加载"""
        return cls._model is not None
    
    @classmethod
    def load_model(cls, model_name="base"):
        """显式加载模型"""
        print(f"正在加载Whisper {model_name}模型...")
        cls._model = whisper.load_model(model_name)
        print("模型加载完成！")
        return cls._model
