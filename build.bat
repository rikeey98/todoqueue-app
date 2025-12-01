@echo off
echo TodoQueue EXE 파일 생성 중...
pyinstaller --onefile --windowed --name="TodoQueue" --icon=src/todoqueue/assets/icon.ico src/todoqueue/main.py
echo 완료! dist 폴더에서 TodoQueue.exe 파일을 확인하세요.
pause
