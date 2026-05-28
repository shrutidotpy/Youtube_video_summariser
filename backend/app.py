from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import requests
import re

app = Flask(__name__)
CORS(app)  # For development. In production, specify allowed origins.

# Function to extract video ID using regex
def extract_video_id(url):
    # Regex patterns for YouTube URLs
    regex_patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
    ]
    for pattern in regex_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Function to fetch video transcript
def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcript available for this video."
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

# Function to get video details using YouTube's oEmbed API
def get_video_details(video_url):
    oembed_url = "https://www.youtube.com/oembed"
    params = {
        'url': video_url,
        'format': 'json'
    }
    try:
        response = requests.get(oembed_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title", "No Title Available"),
            "description": data.get("author_name", "No Description Available"),
            "length": "N/A"  # oEmbed does not provide video length
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching video details: {str(e)}"}
    except ValueError:
        return {"error": "Invalid response from YouTube oEmbed API."}

# Function to summarize the transcript
def summarize_text(text, num_sentences=5):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, num_sentences)
        summarized_text = " ".join(str(sentence) for sentence in summary)
        return summarized_text if summarized_text else "Summary could not be generated."
    except Exception as e:
        return f"Error during summarization: {str(e)}"

# Root route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "YouTube Video Summarizer API is running."}), 200

# Route to summarize video content
@app.route('/summarize', methods=['POST'])
def summarize_video():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    video_url = data.get("video_url")
    if not video_url:
        return jsonify({"error": "Video URL not provided"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    transcript = get_transcript(video_id)
    if "Transcript" in transcript:
        return jsonify({"error": transcript}), 400

    summary = summarize_text(transcript)
    if "Error" in summary or "could not" in summary.lower():
        return jsonify({"error": summary}), 400

    video_details = get_video_details(video_url)
    if "error" in video_details:
        return jsonify({"error": video_details["error"]}), 400

    return jsonify({"video_details": video_details, "summary": summary})

if __name__ == "__main__":
    app.run(debug=True)
