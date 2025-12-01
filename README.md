# TodoQueue

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)

시간 기반 우선순위를 활용한 혁신적인 할일 관리 도구입니다.

## 🎯 특징

- **⏰ 시간순 자동 우선순위**: 생각나는 순간의 우선순위를 존중
- **🖱️ 직관적인 드래그&드롭**: 언제든지 순서 조정 가능
- **📁 카테고리 & 태그**: 체계적인 할일 분류
- **💾 영구 저장**: SQLite로 안전한 데이터 보관
- **🎨 현대적 UI**: tkinter 기반 깔끔한 인터페이스

## 🚀 설치 및 실행

### UV 사용 (권장)
```bash
# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/todoqueue-app.git
cd todoqueue-app

# UV로 의존성 설치 및 실행
uv sync
uv run todoqueue
```

### 기존 Python 환경 사용
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e .[dev]

# 실행
python -m todoqueue.main
```

## 📦 실행 파일 빌드

### Windows EXE 파일 생성
```bash
# UV 환경에서 빌드
uv run pyinstaller --onefile --windowed --name="TodoQueue" src/todoqueue/main.py

# 또는 배치 파일 사용
build.bat
```

실행 파일은 `dist/TodoQueue.exe`에 생성됩니다.

## 💡 사용법

1. **할일 추가**: '할일 추가' 탭에서 내용 입력 후 추가 버튼 클릭 (또는 Ctrl+Enter)
2. **순서 조정**: '할일 목록' 탭에서 드래그&드롭으로 우선순위 변경
3. **완료 처리**: ✅ 버튼 클릭으로 할일 완료
4. **데이터 백업**: 파일 메뉴 → 데이터 백업

## 📂 프로젝트 구조

```
todoqueue-app/
├── src/todoqueue/
│   ├── __init__.py
│   └── main.py          # 메인 애플리케이션
├── tests/
├── pyproject.toml       # 프로젝트 설정
├── build.bat            # Windows 빌드 스크립트
└── README.md
```

## 🛠️ 개발

### 코드 품질 도구 실행
```bash
# 코드 포맷팅
uv run black src/

# 린팅
uv run flake8 src/

# 테스트 (구현 예정)
uv run pytest
```

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여

이슈 및 풀 리퀘스트는 언제나 환영합니다!

## 📧 문의

- 이메일: your.email@example.com
- 이슈: [GitHub Issues](https://github.com/YOUR_USERNAME/todoqueue-app/issues)