from utils.audio_processor import process_input
from core.transcriber import transcribe_all

source = "https://youtu.be/72duHF7iZiU?si=PpCd0OmxOtvEvL5B"
#source = "https://youtu.be/0JwJUn_eYOo?si=dAb049p7xwFqwBeb"
# #source="https://youtu.be/qLr-wwwNB4o?si=2Lp3tL-C9kb0C9PU"

chunks = process_input(source)

print(transcribe_all(chunks))





from dotenv import load_dotenv

# MUST be before any core/ imports
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)


# --------------------------------------------------
# INPUT
# --------------------------------------------------

source = "https://youtu.be/72duHF7iZiU?si=PpCd0OmxOtvEvL5B"

# "english" -> Whisper
# "hinglish" -> Sarvam
language = "english"


# --------------------------------------------------
# 1. PROCESS INPUT
# --------------------------------------------------

print("\nProcessing input...")

chunks = process_input(source)

print(f"Created {len(chunks)} audio chunk(s).")


# --------------------------------------------------
# 2. TRANSCRIBE
# --------------------------------------------------

print("\nTranscribing audio...")

transcript = transcribe_all(
    chunks,
    language="en"
)


# --------------------------------------------------
# 3. DISPLAY TRANSCRIPT
# --------------------------------------------------

print("\n" + "=" * 60)
print("TRANSCRIPT")
print("=" * 60)

if len(transcript) > 500:
    print(transcript[:500] + "...")
else:
    print(transcript)


# --------------------------------------------------
# 4. GENERATE TITLE & SUMMARY
# --------------------------------------------------

print("\nGenerating title and summary...")

title = generate_title(transcript)
summary = summarize(transcript)


# --------------------------------------------------
# 5. EXTRACT INFORMATION
# --------------------------------------------------

print("Extracting action items, decisions and questions...")

action_items = extract_action_items(transcript)
key_decisions = extract_key_decisions(transcript)
questions = extract_questions(transcript)


# --------------------------------------------------
# 6. DISPLAY RESULTS
# --------------------------------------------------

print("\n" + "=" * 60)
print("TITLE")
print("=" * 60)
print(title)


print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(summary)


print("\n" + "=" * 60)
print("ACTION ITEMS")
print("=" * 60)

if action_items:
    for i, item in enumerate(action_items, start=1):
        print(f"{i}. {item}")
else:
    print("No action items found.")


print("\n" + "=" * 60)
print("KEY DECISIONS")
print("=" * 60)

if key_decisions:
    for i, decision in enumerate(key_decisions, start=1):
        print(f"{i}. {decision}")
else:
    print("No key decisions found.")


print("\n" + "=" * 60)
print("QUESTIONS")
print("=" * 60)

if questions:
    for i, question in enumerate(questions, start=1):
        print(f"{i}. {question}")
else:
    print("No questions found.")


print("\n" + "=" * 60)
print("PROCESSING COMPLETE")
print("=" * 60)


# --------------------------------------------------
# 4. GENERATE TITLE & SUMMARY
# --------------------------------------------------

title = generate_title(transcript)
summary = summarize(transcript)

print("\n" + "=" * 60)
print(f"TITLE: {title}")
print("=" * 60)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(summary)


# --------------------------------------------------
# 5. EXTRACT ACTION ITEMS, DECISIONS & QUESTIONS
# --------------------------------------------------

action_items = extract_action_items(transcript)
decisions = extract_key_decisions(transcript)
questions = extract_questions(transcript)


# --------------------------------------------------
# 6. DISPLAY ACTION ITEMS
# --------------------------------------------------

print("\n" + "=" * 60)
print("ACTION ITEMS")
print("=" * 60)
print(action_items)


# --------------------------------------------------
# 7. DISPLAY KEY DECISIONS
# --------------------------------------------------

print("\n" + "=" * 60)
print("KEY DECISIONS")
print("=" * 60)
print(decisions)


# --------------------------------------------------
# 8. DISPLAY OPEN QUESTIONS
# --------------------------------------------------

print("\n" + "=" * 60)
print("OPEN QUESTIONS")
print("=" * 60)
print(questions)