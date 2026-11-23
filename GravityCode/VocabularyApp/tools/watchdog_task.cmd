@echo off
REM VocabularyApp - watchdog 24/7 (AI + media + toast)
cd /d "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\ai_watchdog.py >> data\logs\watchdog_stdout.log 2>&1
