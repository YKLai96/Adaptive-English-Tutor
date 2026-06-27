Markdown
# 🚀 Adaptive English Shadowing Tutor Bot

An intelligent, context-aware Telegram bot designed for intense English shadowing and pronunciation training. Powered by **Google Gemini 2.5 Flash** and **Azure Cognitive Services**, it dynamically tracks your phonetic weaknesses and generates personalized practice materials.

## ✨ Core Features
* **A-Z Pronunciation Assessment:** Utilizes Azure Speech SDK to score phoneme-level accuracy, fluency, and completeness.
* **Incremental Weakness Tracking:** Maintains a local JSON ledger (`user_profile.json`) to silently remember your specific struggling phonemes (e.g., `/th/`, `/r/`).
* **Adaptive Content Generation:** Uses Gemini to dynamically generate 15-20 second practice sentences heavily weighted with your tracked weak phonemes.
* **Custom Contexts:** Practice sentences can be tailored to any professional context via the `/theme` command (e.g., Corporate Finance Interviews, Cryptocurrency Asset Reconciliation, IT Team Syncs).
* **Prosody Analysis:** Deep-dive AI feedback on word stress, linking opportunities, and overall rhythm.
* **Resilient Watchdog:** Built-in auto-reconnection loop to survive 502 Bad Gateway and ReadTimeout errors, ensuring stable 24/7 server hosting.

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Adaptive-English-Tutor-Bot.git](https://github.com/YOUR_USERNAME/Adaptive-English-Tutor-Bot.git)
   cd Adaptive-English-Tutor-Bot
Install FFmpeg:
The bot requires FFmpeg to convert Telegram .ogg voice notes to .wav. Ensure FFmpeg is installed and added to your system's PATH.

Install Python Dependencies:

Bash
pip install -r requirements.txt
Configure API Keys:
Open telegram_tutor_bot.py and replace the placeholders in the configuration section with your actual keys from Telegram BotFather, Azure Speech Services, and Google Gemini Studio.

Run the Bot:

Bash
python telegram_tutor_bot.py
🎮 How to Use
Send /start to the bot in Telegram.

(Optional) Send /theme to customize your speaking scenario.

The bot will send you a custom-generated sentence and a slowed-down British native audio sample.

Reply with a voice message mimicking the native audio.

Receive a hardcore, 4-part diagnostic report on your overall score, specific phonetic errors, prosody, and progress tracking.

Choose to retry the current sentence to fix mistakes or proceed to the next specifically tailored challenge!

Built for continuous, data-driven language improvement.