# AI Prompt Enhancer

A Wispr Flow-style desktop utility that enhances the prompt you have **selected** in **any** application.

1. Select some text (your draft prompt) in any app.
2. Press the global hotkey (default: `Ctrl+Alt+E`).
3. The app copies your selection, sends it to your configured AI model, and shows the enhanced prompt in a floating rectangle window.
4. Click **Approve** to replace your selection with the enhanced prompt, or **Decline** to keep your original text. You can also edit the text before approving.

## Setup

```
pip install -r requirements.txt
```

Edit `.env` and set your values:

```
BASE_URL=https://api.openai.com/v1
API_KEY=sk-your-key
MODEL_ID=gpt-4o-mini
HOTKEY=ctrl+alt+e
TEMPERATURE=0.4
```

Any OpenAI-compatible endpoint works (OpenAI, OpenRouter, Groq, Ollama, etc.).

## Run

```
python app.py
```

Or double-click `run.bat`.

### Notes

- On Windows, if the hotkey fails to register, run the terminal / `run.bat` **as Administrator** (the `keyboard` library needs elevated rights for global hotkeys).
- The popup window is draggable and always on top. Press `Esc` to decline.
- Your API key stays local in `.env` (git-ignored).
