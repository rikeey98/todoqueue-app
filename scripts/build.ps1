**scripts/build.ps1** (PowerShell 빌드 스크립트):
```powershell
# TodoQueue EXE 빌드 스크립트

Write-Host "TodoQueue EXE 파일 생성 중..." -ForegroundColor Green

# UV가 설치되어 있는지 확인
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "UV가 설치되어 있지 않습니다. 설치 중..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
}

# 의존성 설치
Write-Host "의존성 설치 중..." -ForegroundColor Blue
uv sync --group dev

# EXE 파일 생성
Write-Host "EXE 파일 생성 중..." -ForegroundColor Blue
uv run pyinstaller --onefile --windowed --name="TodoQueue" --icon=assets/icon.ico src/todoqueue/main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 성공! dist/TodoQueue.exe 파일이 생성되었습니다." -ForegroundColor Green
    Write-Host "파일 위치: $(Resolve-Path 'dist/TodoQueue.exe')" -ForegroundColor Cyan
} else {
    Write-Host "❌ 빌드 실패!" -ForegroundColor Red
}

Read-Host "계속하려면 Enter를 누르세요"