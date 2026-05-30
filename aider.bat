@echo off

:: 1. CACHE PROTECTION
set AIDER_DIVERSIFY_PROMPTS=false

:: 2. LAUNCH WITH EXPLICIT FLAGS
:: We removed --no-pretty to restore colors and nice formatting.
C:\Users\Shadow\AppData\Local\Programs\Python\Python312\python.exe -m aider --llm-history-file .aider.llm.history --edit-format diff --chat-language English --commit-language English --no-auto-commits --cache-prompts --auto-test --dark-mode --no-show-model-warnings%*