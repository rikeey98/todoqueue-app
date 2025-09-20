**build.bat** (Windows 사용자용):
```batch
@echo off
echo TodoQueue EXE 파일 생성 중...
pyinstaller --onefile --windowed --name="TodoQueue" todo_queue_app.py
echo 완료! dist 폴더에서 TodoQueue.exe 파일을 확인하세요.
pause
