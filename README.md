# AI Real-Time Gym Coach

A Streamlit workout coach with webcam-based pose tracking, repetition and set
counting, workout history, and optional spoken coaching.

## Requirements

- Python 3.11
- A webcam
- A Groq API key for voice coaching

## Run locally

```powershell
uv venv
uv pip install -r requirement.txt
```

Create a `.env` file in the project root and add your key:

```text
GROQ_API_KEY=your_groq_api_key
```

Then start the app:

```powershell
uv run streamlit run main.py
```

The local workout history database is created automatically. The app uses the
system sans-serif font if the optional local font file is unavailable.
