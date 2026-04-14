# Whisper 语音识别鲁棒性实验

## 项目简介
本项目基于 OpenAI Whisper 语音识别模型，通过注入不同强度的背景噪声，评估模型在有噪声环境下的转录鲁棒性。实验使用 LibriSpeech 干净数据集作为测试数据，通过计算词错误率（WER）定量分析模型性能。

## 实验内容
1. **核心模型**：OpenAI Whisper Base 版本
2. **数据集**：LibriSpeech (clean) 干净语音数据集
3. **噪声测试**：使用 pydub 库注入 5dB 到 20dB 的背景噪声
4. **评估指标**：词错误率（WER）对比分析

## 快速开始
### 1. 用pycharm识别本项目（或者你想直接搞个虚拟环境也许）
### 2. 在虚拟环境中安装依赖
pip install -r requirements.txt
### 3. 启动项目
