let localStream;
let websocket;
const videoElement = document.getElementById('localVideo');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');

startButton.addEventListener('click', startStreaming);
stopButton.addEventListener('click', stopStreaming);

let transcriptionElement;
let transcriptionHistory = '';

///

async function startStreaming() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            audio: {
              sampleRate: 16000, // Set the desired sample rate
              sampleSize: 16,    // Optionally specify the sample size (e.g., 16-bit)
              channelCount: 1,   // Mono audio, adjust as necessary
            },
            video: false
          })
          .then(function(stream) {
            // Do something with the audio stream
            console.log('Audio stream with 16000 Hz sample rate obtained');
          })
          .catch(function(err) {
            console.error('Error accessing audio stream:', err);
          });
        videoElement.srcObject = localStream;

        console.log('Media devices accessed successfully.');

        // Create transcription element
        transcriptionElement = document.createElement('div');
        transcriptionElement.id = 'transcription';
        transcriptionElement.style.position = 'absolute';
        transcriptionElement.style.bottom = '10px';
        transcriptionElement.style.left = '10px';
        transcriptionElement.style.right = '10px';
        transcriptionElement.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        transcriptionElement.style.color = 'white';
        transcriptionElement.style.padding = '10px';
        transcriptionElement.style.maxHeight = '150px';
        transcriptionElement.style.overflowY = 'auto';
        document.body.appendChild(transcriptionElement);

        websocket = new WebSocket('/');

        websocket.onopen = () => {
            console.log('WebSocket connection established');
            startButton.disabled = true;
            stopButton.disabled = false;
            sendAudioData();
            sendVideoData();
        };

        websocket.onmessage = (event) => {
            console.log('WebSocket message received:', event.data);
            const message = JSON.parse(event.data);
            if (message.type === 'transcription') {
                updateTranscription(message.data);
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
        console.error('Error accessing media devices:', error);
    }
}

///

function stopStreaming() {
    console.log('Stopping streaming...');
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    if (websocket) {
        websocket.close();
    }
    videoElement.srcObject = null;
    startButton.disabled = false;
    stopButton.disabled = true;
    if (transcriptionElement) {
        transcriptionElement.remove();
        transcriptionElement = null;
    }
    transcriptionHistory = '';
}

///

function updateTranscription(text) {
    if (transcriptionElement) {
        transcriptionHistory += text + ' ';
        transcriptionElement.textContent = transcriptionHistory;
        transcriptionElement.scrollTop = transcriptionElement.scrollHeight;
    }
}

///

function sendAudioData() {

    const audioTrack = localStream.getAudioTracks()[0];
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const sourceNode = audioContext.createMediaStreamSource(new MediaStream([audioTrack]));
    const scriptNode = audioContext.createScriptProcessor(4096, 1, 1);

    sourceNode.connect(scriptNode);
    scriptNode.connect(audioContext.destination);

    scriptNode.onaudioprocess = (event) => {
        const audioData = event.inputBuffer.getChannelData(0); 

        // Convert Float32Array to ArrayBuffer and then to Base64
        const float32Array = new Float32Array(audioData);
        const arrayBuffer = float32Array.buffer;
        const base64String = arrayBufferToBase64(arrayBuffer);

        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ 
                type: 'audio',
                data: base64String, 
            }));
        } else {
            console.error('WebSocket is not open. Cannot send audio data.');
        }
    };
}

///

function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

///

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
                websocket.send(JSON.stringify({ 
                    type: 'video',
                    data: imageData,
                }));
            } else {
                console.error('WebSocket is not open. Cannot send video data.');
            }
        }
        setTimeout(captureFrame, 2000);
    }

    captureFrame();
}