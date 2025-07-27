// MediaPipe Hands integration for real-time hand detection
// This script requires you to include the MediaPipe Hands and drawing_utils scripts in your HTML
// CDN: https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js
//      https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js

let handDetectionActive = false;
let handLivenessCallback = null;

function setupHandDetection(videoElement, onHandDetected) {
    if (handDetectionActive) return;
    handDetectionActive = true;
    handLivenessCallback = onHandDetected;

    const hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });
    hands.setOptions({
        maxNumHands: 1,
        modelComplexity: 1,
        minDetectionConfidence: 0.7,
        minTrackingConfidence: 0.7
    });

    hands.onResults(results => {
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            // Hand detected
            if (typeof handLivenessCallback === 'function') {
                handLivenessCallback();
            }
        }
    });

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await hands.send({image: videoElement});
        },
        width: 180,
        height: 135
    });
    camera.start();
}
