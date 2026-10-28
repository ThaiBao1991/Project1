@echo off
title Skill & Rule Hub
cd /d "%~dp0"
python SkillRuleApp.py
if errorlevel 1 pause

