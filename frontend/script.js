document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('video-form');
    const videoUrlInput = document.getElementById('video-url');
    const videoIframe = document.getElementById('video');
    const summaryContainer = document.getElementById('summary');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const videoUrl = videoUrlInput.value.trim();
        summaryContainer.innerHTML = ""; // Clear previous summary

        if (!videoUrl) {
            alert('Please enter a YouTube video URL.');
            return;
        }

        let videoId = extractVideoID(videoUrl);
        if (!videoId) {
            alert('Invalid YouTube URL. Please enter a valid URL.');
            return;
        }

        // Embed the video
        videoIframe.src = `https://www.youtube.com/embed/${videoId}`;

        // Show loading indicator
        summaryContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
            </div>
        `;

        // Fetch the summary
        fetch('http://127.0.0.1:5000/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_url: videoUrl })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                summaryContainer.innerHTML = `<div class="alert alert-danger" role="alert">${data.error}</div>`;
            } else {
                const { video_details, summary } = data;
                displaySummary(video_details, summary);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            summaryContainer.innerHTML = `<div class="alert alert-danger" role="alert">An unexpected error occurred. Please try again later.</div>`;
        });
    });

    // Function to extract Video ID
    function extractVideoID(url) {
        const regex = /(?:v=|\/)([0-9A-Za-z_-]{11}).*/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    // Function to display the summary and video details
    function displaySummary(details, summary) {
        let htmlContent = `
            <h2>${details.title}</h2>
            <p><strong>Description:</strong> ${details.description}</p>
            <p><strong>Length:</strong> ${details.length}</p>
            <h3>Summary:</h3>
            <p>${summary}</p>
        `;
        summaryContainer.innerHTML = htmlContent;
    }
});
