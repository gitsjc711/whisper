// 额外的JavaScript功能

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl + Enter 开始转录
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        if (document.getElementById('transcriptionResult').style.display !== 'none') {
            startRobustnessTest();
        } else if (currentFile) {
            transcribeAudio();
        }
    }

    // Escape 键清除文件
    if (e.key === 'Escape') {
        clearFile();
    }
});

// 音频可视化
function visualizeAudio(audioElement, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaElementSource(audioElement);

    source.connect(analyser);
    analyser.connect(audioContext.destination);
    analyser.fftSize = 256;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        const WIDTH = canvas.width;
        const HEIGHT = canvas.height;

        requestAnimationFrame(draw);

        analyser.getByteTimeDomainData(dataArray);

        ctx.fillStyle = 'rgb(248, 249, 250)';
        ctx.fillRect(0, 0, WIDTH, HEIGHT);

        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgb(52, 152, 219)';
        ctx.beginPath();

        const sliceWidth = WIDTH * 1.0 / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = v * HEIGHT / 2;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
    }

    draw();
}