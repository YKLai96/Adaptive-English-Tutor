import os
import random
import time
import json
import telebot
from telebot import types
import subprocess
import azure.cognitiveservices.speech as speechsdk
from google import genai

# ================= 🔑 CONFIGURATION =================
# WARNING: Never push your actual API keys to GitHub!
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
AZURE_SPEECH_KEY = "YOUR_AZURE_SPEECH_KEY_HERE"
AZURE_REGION = "YOUR_AZURE_REGION_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

PROFILE_PATH = "user_profile.json"

# ================= 💾 GLOBAL STATES =================
user_states = {} 
target_sentences = {}  
previous_results = {}  
user_themes = {}  # Stores custom themes for specific users

# ================= 💾 DYNAMIC PROFILE MANAGEMENT =================

def load_user_profile():
    """Load the incremental weakness ledger from the local JSON file."""
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"weak_phonemes": {}}

def save_user_profile(profile):
    """Save updates to the local JSON ledger."""
    with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=4)

def update_weak_phonemes(assessment_words):
    """Dynamically update the user's phoneme weakness tracker based on Azure scores."""
    profile = load_user_profile()
    current_weak = profile.get("weak_phonemes", {})
    
    for word in assessment_words:
        for phoneme in word.phonemes:
            p_name = phoneme.phoneme
            score = phoneme.accuracy_score
            
            if score < 80:
                # Add or increment failure count
                current_weak[p_name] = current_weak.get(p_name, 0) + 1
            elif score >= 85 and p_name in current_weak:
                # Remove phoneme once mastered
                del current_weak[p_name]
                
    profile["weak_phonemes"] = current_weak
    save_user_profile(profile)
    return list(current_weak.keys())

# ================= 🧠 AI CONTENT & SPEECH ENGINE =================

def generate_adaptive_sentence(chat_id):
    """Generate a custom, 15-20s sentence targeting the user's specific weak phonemes."""
    profile = load_user_profile()
    weak_list = list(profile.get("weak_phonemes", {}).keys())
    
    # Default theme if user hasn't set one
    default_theme = "Financial auditing, cryptocurrency exchange asset reconciliation, or marathon RFID timing systems"
    current_theme = user_themes.get(chat_id, default_theme)
    
    base_prompt = f"""
    Act as a senior British English interpreter and tutor. Generate exactly ONE English sentence for shadowing practice.
    Requirements:
    1. Length: Around 25-35 words (approx. 15-20 seconds of speaking time for a native speaker).
    2. Context: Highly relevant to {current_theme}.
    3. Tone: Professional, utilizing advanced corporate vocabulary and complex clauses.
    [CRITICAL] Do not provide explanations, translations, or extra punctuation. Output ONLY the sentence.
    """
    
    if weak_list:
        sounds_str = ", ".join([f"/{p}/" for p in weak_list])
        prompt = f"My current weakest phonemes are: {sounds_str}.\n{base_prompt}\nIntentionally heavily load the sentence with professional words containing these exact phonemes."
    else:
        prompt = f"I have no specific phoneme weaknesses currently.\n{base_prompt}\nGenerate a standard advanced professional sentence."
        
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text.strip().replace("\n", " ").replace("**", "")
    except Exception as e:
        print(f"Content generation failed: {e}")
        return "I am deeply passionate about this role and believe my previous experience aligns perfectly with your strategic objectives for the upcoming quarter."

def synthesize_speech(text, output_filename="tts_demo.wav"):
    """Synthesize British English audio slowed down by 10% for precise shadowing."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    ssml_text = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-GB'>
        <voice name='en-GB-SoniaNeural'><prosody rate='-10%'>{text}</prosody></voice>
    </speak>
    """
    return synthesizer.speak_ssml_async(ssml_text).get().reason == speechsdk.ResultReason.SynthesizingAudioCompleted

def analyze_prosody_with_ai(recognized_text, reference_text):
    """Analyze rhythm, stress, and linking using Gemini."""
    prompt = f"""
    Analyze the following English shadowing attempt by a non-native speaker:
    Target Sentence: "{reference_text}"
    Recognized Audio: "{recognized_text}"
    
    Provide a highly concise, professional analysis (under 150 words) on two metrics:
    1. Rhythm & Word Stress: Identify misplaced stress on content words or unnatural pauses.
    2. Linking & Intonation: Point out missed linking opportunities (vowel-to-vowel, consonant-to-vowel).
    """
    try:
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text
    except:
        return "Prosody analysis is currently unavailable."

def detailed_pronunciation_assessment(audio_filepath, reference_text):
    """Core Azure evaluation engine generating a comprehensive 3-part diagnostic report."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_filepath)
    
    pron_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    pron_config.apply_to(recognizer)
    result = recognizer.recognize_once_async().get()
    
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return "❌ Audio not clearly recognized. Please ensure a quiet environment and read loudly.", [], 0, []
        
    pron_result = speechsdk.PronunciationAssessmentResult(result)
    active_weak_sounds = update_weak_phonemes(pron_result.words)
    
    overall_score = pron_result.pronunciation_score
    current_attempt_weaks = [] 
    
    report = "📊 **[Part 1: Overall Score]**\n"
    report += f"• Comprehensive Score: *{overall_score}/100*\n"
    report += f"  (Accuracy: {pron_result.accuracy_score} | Fluency: {pron_result.fluency_score})\n\n"
    
    report += "👅 **[Part 2: Phonetic Accuracy]**\n"
    report += "Note: *Bolded words* indicate pronunciation flaws.\n\n>>> "
    
    detailed_weak_notes = []
    for word in pron_result.words:
        if word.error_type != "None" or word.accuracy_score < 80:
            report += f" *{word.word.upper()}* "
            bad_ph = [f"/{p.phoneme}/" for p in word.phonemes if p.accuracy_score < 80]
            if bad_ph:
                current_attempt_weaks.extend(bad_ph)
                detailed_weak_notes.append(f"• Flaws in `{word.word}`: {', '.join(bad_ph)}")
        else:
            report += f" {word.word} "
            
    current_attempt_weaks = list(set(current_attempt_weaks))
            
    report += "\n\n" + "\n".join(detailed_weak_notes) if detailed_weak_notes else "\n• No significant phonetic errors detected."
    report += f"\n\n📂 Ledger Update: Current tracked weak phonemes: {', '.join([f'/{s}/' for s in active_weak_sounds]) if active_weak_sounds else 'None'}\n\n"
    
    report += "🎼 **[Part 3: Prosody Analysis]**\n"
    report += analyze_prosody_with_ai(result.text, reference_text)
    
    return report, active_weak_sounds, overall_score, current_attempt_weaks

# ================= 🤖 TELEGRAM BOT ROUTING =================

def send_next_challenge(chat_id):
    global target_sentences
    bot.send_message(chat_id, "⏳ Reviewing your ledger and generating a targeted challenge...")
    
    sentence = generate_adaptive_sentence(chat_id)
    target_sentences[chat_id] = sentence
    
    msg_text = (
        "🎯 **Shadowing Challenge** (15-20s)\n\n"
        f"Listen to the slowed-down British native sample, grasp the rhythm, and record your mimicry:\n\n"
        f"`{sentence}`"
    )
    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    
    tts_file = f"tts_{chat_id}.wav"
    if synthesize_speech(sentence, tts_file):
        with open(tts_file, 'rb') as audio:
            bot.send_voice(chat_id, audio)
        os.remove(tts_file)

@bot.message_handler(commands=['theme'])
def change_theme(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id, 
        "📝 **Please reply with your desired practice context.**\n\n"
        "Examples:\n"
        "• Senior Finance Manager job interview\n"
        "• Quarterly financial reporting to the board\n"
        "• Cross-border IT team sync\n"
        "• Casual travel and dining", 
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_theme_step)

def process_theme_step(message):
    chat_id = message.chat.id
    new_theme = message.text.strip()
    user_themes[chat_id] = new_theme
    
    bot.send_message(
        chat_id, 
        f"✅ Theme successfully updated to:\n**{new_theme}**\n\n"
        "The AI will contextualize your next sentences accordingly. Send /start or click 'Next Challenge' to begin!", 
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['start'])
def start_tutor(message):
    chat_id = message.chat.id
    if os.path.exists(PROFILE_PATH):
        try: os.remove(PROFILE_PATH)
        except: pass
    save_user_profile({"weak_phonemes": {}})
    
    if chat_id in previous_results:
        del previous_results[chat_id]
        
    bot.send_message(chat_id, "🚀 Adaptive English Shadowing Tutor initialized! Send /theme anytime to change your practice context.")
    send_next_challenge(chat_id)

@bot.message_handler(content_types=['voice'])
def handle_voice_input(message):
    chat_id = message.chat.id
    global target_sentences, previous_results
    target = target_sentences.get(chat_id)
    
    if not target:
        bot.reply_to(message, "Please send /start to initiate a session.")
        return
        
    bot.reply_to(message, "🎙️ Extracting audio track for deep phonetic analysis...")
    ogg_path, wav_path = f"temp_{chat_id}.ogg", f"temp_{chat_id}.wav"
    
    try:
        # FFMPEG Conversion
        file_info = bot.get_file(message.voice.file_id)
        with open(ogg_path, 'wb') as f:
            f.write(bot.download_file(file_info.file_path))
        subprocess.run(["ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Core Assessment
        report, active_weaks, current_score, current_weaks = detailed_pronunciation_assessment(wav_path, target)
        
        # Progress Tracking (Comparing with previous attempt if available)
        prev_data = previous_results.get(chat_id)
        if prev_data:
            score_diff = current_score - prev_data["score"]
            fixed_sounds = set(prev_data["weak"]) - set(current_weaks)
            new_err_sounds = set(current_weaks) - set(prev_data["weak"])
            
            comp_txt = "\n\n📈 **[Part 4: Progress Tracking]**\n"
            if score_diff > 0:
                comp_txt += f"🟢 Overall Score: Improved by {score_diff:.1f} points! 🎉\n"
            elif score_diff < 0:
                comp_txt += f"🔴 Overall Score: Dropped by {abs(score_diff):.1f} points. Watch the details.\n"
            else:
                comp_txt += "⚖️ Overall Score: Maintained.\n"
                
            if fixed_sounds:
                comp_txt += f"✅ Corrected phonemes: {', '.join(fixed_sounds)}\n"
            if new_err_sounds:
                comp_txt += f"⚠️ Regressed/New errors: {', '.join(new_err_sounds)}\n"
                
            report += comp_txt
            
        previous_results[chat_id] = {"score": current_score, "weak": current_weaks}
        
        # Inline Buttons
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔄 Retry Attempt", callback_data="retry_challenge"),
            types.InlineKeyboardButton("➡️ Next Challenge", callback_data="next_challenge")
        )
        
        bot.send_message(chat_id, report, reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Assessment interrupted: {str(e)}")
    finally:
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)

@bot.callback_query_handler(func=lambda call: call.data == "retry_challenge")
def retry_step_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, "Preparing retry...")
    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except: pass
    
    target = target_sentences.get(chat_id)
    if target:
        bot.send_message(chat_id, f"🔄 **Take a deep breath and read again:**\n\n`{target}`", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "Target sentence lost. Please send /start.")

@bot.callback_query_handler(func=lambda call: call.data == "next_challenge")
def next_step_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, "Loading next challenge...")
    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except: pass
    
    if chat_id in previous_results:
        del previous_results[chat_id]
        
    send_next_challenge(chat_id)

# ================= 🛡️ WATCHDOG / AUTO-RECONNECT =================

if __name__ == "__main__":
    print("🚀 Adaptive Shadowing System is running in the background... (Resilient polling enabled)")
    while True:
        try:
            bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
        except KeyboardInterrupt:
            print("\n🛑 System shut down safely by user.")
            break
        except Exception as e:
            print(f"\n⚠️ Network interrupt or timeout caught: {e}")
            print("🔄 Watchdog active: Restarting network polling in 5 seconds...")
            time.sleep(5)