@echo off
chcp 65001 > nul
cd /d "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\check_done.py >> data\logs\scheduler.log 2>&1
