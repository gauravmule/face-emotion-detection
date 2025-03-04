const socket = io.connect('http://' + window.location.hostname + ':' + (window.location.port || 80));
const video = document.getElementById('video-stream');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const summaryContent = document.getElementById('summary-content');
let stream;

startBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        startBtn.disabled = true;
        stopBtn.disabled = false;

        const response = await fetch('/start_session', { method: 'POST' });
        const data = await response.json();
        if (!data.success) throw new Error(data.message);

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');

        setInterval(() => {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const frame = canvas.toDataURL('image/jpeg');
            socket.emit('video_frame', frame);
        }, 100);
    } catch (error) {
        alert('Error: ' + error.message);
        startBtn.disabled = false;
    }
});

stopBtn.addEventListener('click', async () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
    startBtn.disabled = false;
    stopBtn.disabled = true;
    summaryContent.innerHTML = '<p>No active session</p>';
    await fetch('/stop_session', { method: 'POST' });
});

socket.on('processed_frame', (data) => {
    video.src = data;
});

socket.on('emotion_summary', (summary) => {
    let html = `<p>Detected Faces: ${summary.total_faces}</p><ul>`;
    if (summary.total_faces > 0) {
        for (const [emotion, count] of Object.entries(summary.emotions)) {
            html += `<li>${emotion}: ${count}</li>`;
        }
    } else {
        html += "<li>No faces detected</li>";
    }
    summaryContent.innerHTML = html + "</ul>";
});