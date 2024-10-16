<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Real-time Emotion Analysis and Face Recognition</title>
    <style>
        #localVideo {
            width: 100%;
            max-width: 600px;
            border: 2px solid #ccc;
            margin-bottom: 10px;
        }
        #startButton, #stopButton {
            margin: 5px;
        }
    </style>
</head>
<body>
    <h1>Real-time Emotion and Face Recognition</h1>
    <video id="localVideo" autoplay muted playsinline></video>
    <br>
    <button id="startButton">Start Analysis</button>
    <button id="stopButton" disabled>Stop Analysis</button>

    <script src="client.js"></script>
</body>
</html>