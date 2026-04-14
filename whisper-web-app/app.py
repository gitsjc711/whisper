import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from backend.model.whisper_model import WhisperModelManager
from backend.utils.file_utils import check_ffmpeg
from backend.service.audio_service import AudioService
from backend.service.transcription_service import TranscriptionService
from backend.service.dataset_service import DatasetService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, 'templates'),
    static_folder=os.path.join(FRONTEND_DIR, 'static'),
    static_url_path='/static'
)

app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['RESULTS_FOLDER'] = os.path.join(BASE_DIR, 'results')
app.config['SAMPLES_FOLDER'] = os.path.join(BASE_DIR, 'librispeech_samples')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['SAMPLES_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_audio():
    """上传音频文件"""
    if 'audio_file' not in request.files:
        return jsonify({'error': '没有文件被选择'}), 400

    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    # 获取加噪参数
    noise_level = request.form.get('noise_level')
    if noise_level is not None:
        noise_level = float(noise_level)
        print(f"启用加噪: {noise_level}dB")

    file_path, filename = AudioService.save_audio_file(
        file,
        app.config['UPLOAD_FOLDER'],
        app.config['ALLOWED_EXTENSIONS'],
        noise_level=noise_level
    )
    
    if not file_path:
        return jsonify({'error': '文件类型不支持'}), 400

    rel_path = os.path.relpath(file_path, BASE_DIR)

    return jsonify({
        'success': True,
        'filename': filename,
        'filepath': rel_path,
        'noise_applied': noise_level is not None,
        'noise_level': noise_level
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """转录音频"""
    data = request.json
    file_path = data.get('filepath')

    if not os.path.isabs(file_path):
        file_path = os.path.join(BASE_DIR, file_path)

    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': f'文件不存在: {file_path}'}), 400

    result = TranscriptionService.transcribe_audio(file_path)
    if not result:
        return jsonify({'error': '转录失败'}), 500

    return jsonify({
        'success': True,
        'transcription': result
    })


@app.route('/test-dataset', methods=['POST'])
def test_dataset():
    """测试LibriSpeech数据集"""
    data = request.json if request.is_json else {}
    max_samples = data.get('max_samples', 100)  # 默认100条
    
    # 获取加噪参数
    enable_noise = data.get('enable_noise', False)
    noise_level = data.get('noise_level', None)
    if enable_noise and noise_level is not None:
        noise_level = float(noise_level)
        print(f"数据集测试启用加噪: {noise_level}dB")
    else:
        noise_level = None
    
    # 限制范围在1-500之间
    max_samples = max(1, min(500, int(max_samples)))
    
    print(f"开始测试数据集，样本数量: {max_samples}")
    
    samples = DatasetService.get_librispeech_samples(
        app.config['SAMPLES_FOLDER'],
        max_samples=max_samples
    )
    
    if not samples:
        return jsonify({
            'error': '未找到LibriSpeech样本文件且自动下载失败'
        }), 404
    
    results_data, error = DatasetService.run_dataset_test(
        samples,
        app.config['RESULTS_FOLDER'],
        noise_level=noise_level
    )
    
    if error:
        return jsonify({'error': f'测试失败: {error}'}), 500
    
    results_file = [f for f in os.listdir(app.config['RESULTS_FOLDER']) 
                   if f.startswith('test_results_')][-1]
    
    return jsonify({
        'success': True,
        'results': results_data,
        'results_file': results_file
    })


@app.route('/uploads/<path:filename>')
def get_uploaded_file(filename):
    """获取上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/results/<path:filename>')
def get_result_file(filename):
    """获取测试结果文件"""
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)


@app.route('/results')
def results_page():
    """显示测试结果页面"""
    return render_template('results.html')


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    ffmpeg_available = check_ffmpeg()
    return jsonify({
        'status': 'healthy',
        'model_loaded': WhisperModelManager.is_loaded(),
        'ffmpeg_available': ffmpeg_available
    })


if __name__ == '__main__':
    check_ffmpeg()
    WhisperModelManager.load_model()
    app.run(host='0.0.0.0', port=5000, debug=True)
