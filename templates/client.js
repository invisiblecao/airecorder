let localStream;
let websocket;
const videoElement = document.getElementById('localVideo');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');

startButton.addEventListener('click', startStreaming);
stopButton.addEventListener('click', stopStreaming);

async function startStreaming() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
        videoElement.srcObject = localStream;

        console.log('Video stream accessed successfully.');

        websocket = new WebSocket('ws://localhost:50101');

        websocket.onopen = () => {
            console.log('WebSocket connection established');
            startButton.disabled = true;
            stopButton.disabled = false;

            sendVideoData();
        };

        websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'analysis') {
                console.log('Description:', message.description);
                console.log('Recognition:', message.recognition);
                // You can update the UI with the received description and recognition analysis here
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        websocket.onclose = (event) => {
            console.log('WebSocket connection closed:', event);
            startButton.disabled = false;
            stopButton.disabled = true;
        };

    } catch (error) {
        console.error('Error accessing video stream:', error);
    }
}

function stopStreaming() {
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    if (websocket) {
        websocket.close();
    }
    videoElement.srcObject = null;
    startButton.disabled = false;
    stopButton.disabled = true;
}

function sendVideoData() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    videoElement.onloadedmetadata = () => {
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
    };

    function captureFrame() {
        if (localStream && localStream.getVideoTracks()[0].readyState === 'live') {
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg', 0.5);
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: 'video', data: imageData }));
            }
        }
        setTimeout(captureFrame, 100);
    }

    captureFrame();
}