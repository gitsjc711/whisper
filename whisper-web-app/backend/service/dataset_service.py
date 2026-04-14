import os
import json
import shutil
import urllib.request
import tarfile
import tempfile
from datetime import datetime
from ..utils.file_utils import format_file_size
from .transcription_service import TranscriptionService
from .audio_service import AudioService


class DatasetService:
    """数据集测试服务"""

    @staticmethod
    def calculate_wer(reference, hypothesis):
        """计算词错误率并返回详细分析"""
        import string
        
        # 将连字符替换为空格，再去除其他标点符号
        ref_clean = reference.lower().replace('-', ' ')
        hyp_clean = hypothesis.lower().replace('-', ' ')
        
        translator = str.maketrans('', '', string.punctuation)
        ref_clean = ref_clean.translate(translator)
        hyp_clean = hyp_clean.translate(translator)
        
        ref_words = ref_clean.split()
        hyp_words = hyp_clean.split()

        m, n = len(ref_words), len(hyp_words)

        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1

        wer = dp[m][n] / max(len(ref_words), 1) * 100

        # 回溯分析错误类型
        i, j = m, n
        substitutions = 0
        deletions = 0
        insertions = 0
        correct = 0

        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i-1] == hyp_words[j-1]:
                correct += 1
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                substitutions += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                deletions += 1
                i -= 1
            elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
                insertions += 1
                j -= 1
            else:
                if i > 0:
                    deletions += 1
                    i -= 1
                elif j > 0:
                    insertions += 1
                    j -= 1

        return {
            'wer': round(wer, 2),
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions,
            'correct': correct,
            'total_words': len(ref_words),
            'total_errors': dp[m][n]
        }

    @staticmethod
    def download_librispeech_samples(samples_dir):
        """下载LibriSpeech测试样本"""
        try:
            print("正在下载LibriSpeech测试样本...")
            os.makedirs(samples_dir, exist_ok=True)

            test_url = "https://www.openslr.org/resources/12/test-clean.tar.gz"
            temp_dir = tempfile.mkdtemp()
            tar_path = os.path.join(temp_dir, "test-clean.tar.gz")

            print(f"下载地址: {test_url}")
            urllib.request.urlretrieve(test_url, tar_path)
            print("下载完成，正在解压...")

            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=temp_dir)

            extracted_base = os.path.join(temp_dir, "LibriSpeech", "test-clean")
            sample_count = 0
            max_samples = 10

            if os.path.exists(extracted_base):
                for root, dirs, files in os.walk(extracted_base):
                    if sample_count >= max_samples:
                        break

                    for file in files:
                        if sample_count >= max_samples:
                            break

                        if file.endswith('.flac'):
                            src_path = os.path.join(root, file)
                            dst_name = f"sample_{sample_count + 1:03d}.flac"
                            dst_path = os.path.join(samples_dir, dst_name)

                            shutil.copy2(src_path, dst_path)

                            txt_file = file.replace('.flac', '.txt')
                            txt_src = os.path.join(root, txt_file)
                            if os.path.exists(txt_src):
                                txt_dst = os.path.join(samples_dir, f"sample_{sample_count + 1:03d}.txt")
                                shutil.copy2(txt_src, txt_dst)

                            sample_count += 1
                            print(f"  已复制: {dst_name}")

            shutil.rmtree(temp_dir)
            print(f"成功下载并处理 {sample_count} 个样本到: {samples_dir}")
            return sample_count > 0

        except Exception as e:
            print(f"下载失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def extract_compressed_samples(samples_dir):
        """解压压缩包"""
        compressed_files = [f for f in os.listdir(samples_dir) 
                          if f.endswith(('.tar.gz', '.tgz', '.zip'))]
        
        if not compressed_files:
            return False
        
        for compressed_file in compressed_files:
            compressed_path = os.path.join(samples_dir, compressed_file)
            print(f"发现压缩包: {compressed_file}，正在解压到当前目录...")
            
            try:
                if compressed_file.endswith(('.tar.gz', '.tgz')):
                    with tarfile.open(compressed_path, "r:gz") as tar:
                        tar.extractall(path=samples_dir)
                elif compressed_file.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(compressed_path, 'r') as zip_ref:
                        zip_ref.extractall(samples_dir)
                
                print(f"解压完成: {compressed_file}")
                return True
            except Exception as e:
                print(f"解压失败 {compressed_file}: {e}")
                continue
        
        return False

    @staticmethod
    def scan_audio_files(samples_dir, max_samples=100):
        """递归扫描目录中的音频文件和对应的标注"""
        # 先收集所有 trans.txt 文件，建立音频ID到文本的映射
        transcript_map = {}
        
        for root, dirs, files in os.walk(samples_dir):
            for file in files:
                if file.endswith('.trans.txt'):
                    txt_path = os.path.join(root, file)
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    parts = line.split(' ', 1)
                                    if len(parts) == 2:
                                        audio_id = parts[0]
                                        text = parts[1]
                                        transcript_map[audio_id] = text
                    except Exception as e:
                        print(f"读取标注文件失败 {txt_path}: {e}")
        
        print(f"找到 {len(transcript_map)} 条标注文本")
        
        # 扫描音频文件并匹配标注
        samples = []
        
        for root, dirs, files in os.walk(samples_dir):
            for file in files:
                if len(samples) >= max_samples:
                    break
                    
                if file.endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
                    filepath = os.path.join(root, file)
                    
                    # 从文件名提取音频ID（去掉扩展名）
                    audio_id = os.path.splitext(file)[0]
                    
                    # 在标注映射中查找
                    ground_truth = transcript_map.get(audio_id, "")
                    
                    samples.append({
                        'filepath': filepath,
                        'filename': file,
                        'ground_truth': ground_truth
                    })
            
            if len(samples) >= max_samples:
                break
        
        print(f"扫描到 {len(samples)} 个音频文件，其中 {sum(1 for s in samples if s['ground_truth'])} 个有标注")
        return samples

    @staticmethod
    def get_librispeech_samples(samples_dir, auto_download=True, max_samples=100):
        """获取LibriSpeech测试样本"""
        if not os.path.exists(samples_dir):
            os.makedirs(samples_dir, exist_ok=True)
        
        # 先检查是否有压缩包需要解压
        if DatasetService.extract_compressed_samples(samples_dir):
            print("已解压压缩包，开始扫描样本...")
        
        # 递归扫描音频文件，限制数量
        samples = DatasetService.scan_audio_files(samples_dir, max_samples)
        
        print(f"找到 {len(samples)} 个音频样本（最多扫描 {max_samples} 个）")
        
        if not samples and auto_download:
            print("未找到样本文件，尝试自动下载...")
            if DatasetService.download_librispeech_samples(samples_dir):
                return DatasetService.get_librispeech_samples(samples_dir, auto_download=False, max_samples=max_samples)
            else:
                print("自动下载失败，请手动放置样本文件")

        return samples

    @staticmethod
    def run_dataset_test(samples, results_folder, noise_level=None):
        """
        运行数据集测试
        :param samples: 样本列表
        :param results_folder: 结果保存文件夹
        :param noise_level: 噪声强度 (dB)，None 表示不加噪
        :return: (结果数据, 错误信息)
        """
        try:
            if not samples:
                return None, "未找到测试样本"

            results = []
            total_duration = 0
            total_wer = 0
            wer_count = 0
            total_substitutions = 0
            total_deletions = 0
            total_insertions = 0

            print(f"开始测试 {len(samples)} 个样本{'，加噪强度: ' + str(noise_level) + 'dB' if noise_level else ''}...")

            for i, sample in enumerate(samples, 1):
                print(f"处理样本 {i}/{len(samples)}: {sample['filename']}")

                # 如果需要加噪，先对音频进行加噪处理
                audio_path = sample['filepath']
                if noise_level is not None:
                    noisy_path = AudioService.add_noise(audio_path, float(noise_level))
                    audio_path = noisy_path

                transcription = TranscriptionService.transcribe_audio(audio_path)

                if transcription:
                    file_size = os.path.getsize(sample['filepath'])

                    result = {
                        'filename': sample['filename'],
                        'transcription': transcription['text'],
                        'language': transcription['language'],
                        'duration': transcription['duration'],
                        'segments': transcription['segments'],
                        'file_size': format_file_size(file_size),
                        'noise_applied': noise_level is not None,
                        'noise_level': noise_level
                    }

                    if sample['ground_truth']:
                        wer_analysis = DatasetService.calculate_wer(
                            sample['ground_truth'],
                            transcription['text']
                        )
                        result['ground_truth'] = sample['ground_truth']
                        result['wer'] = wer_analysis['wer']
                        result['substitutions'] = wer_analysis['substitutions']
                        result['deletions'] = wer_analysis['deletions']
                        result['insertions'] = wer_analysis['insertions']
                        result['correct'] = wer_analysis['correct']
                        result['total_words'] = wer_analysis['total_words']
                        result['total_errors'] = wer_analysis['total_errors']
                        
                        total_wer += wer_analysis['wer']
                        total_substitutions += wer_analysis['substitutions']
                        total_deletions += wer_analysis['deletions']
                        total_insertions += wer_analysis['insertions']
                        wer_count += 1

                    results.append(result)
                    total_duration += transcription['duration']
                else:
                    results.append({
                        'filename': sample['filename'],
                        'error': '转录失败'
                    })

            avg_wer = round(total_wer / max(wer_count, 1), 2) if wer_count > 0 else None

            test_summary = {
                'total_samples': len(samples),
                'successful_transcriptions': len([r for r in results if 'error' not in r]),
                'failed_transcriptions': len([r for r in results if 'error' in r]),
                'total_duration': round(total_duration, 2),
                'average_wer': avg_wer,
                'total_substitutions': total_substitutions,
                'total_deletions': total_deletions,
                'total_insertions': total_insertions,
                'total_correct': sum([r.get('correct', 0) for r in results if 'error' not in r]),
                'noise_applied': noise_level is not None,
                'noise_level': noise_level,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            results_data = {
                'summary': test_summary,
                'results': results
            }

            results_file = os.path.join(
                results_folder,
                f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)

            print(f"测试完成！结果已保存到: {results_file}")

            return results_data, None

        except Exception as e:
            print(f"数据集测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)