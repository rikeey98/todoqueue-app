#!/bin/bash
# TodoQueue - UV Sync with SSL verification disabled
# 경고: SSL 검증을 비활성화하면 보안 위험이 있습니다.
# 신뢰할 수 있는 네트워크 환경에서만 사용하세요.

echo "========================================"
echo "TodoQueue - UV Sync (SSL 검증 비활성화)"
echo "========================================"
echo ""
echo "경고: SSL 검증이 비활성화됩니다."
echo "신뢰할 수 있는 네트워크에서만 실행하세요."
echo ""

# PyPI 호스트에 대한 SSL 검증 비활성화
export UV_INSECURE_HOST="pypi.org,files.pythonhosted.org"

echo "UV Sync 실행 중..."
uv sync --extra dev --allow-insecure-host pypi.org --allow-insecure-host files.pythonhosted.org

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 성공적으로 완료되었습니다!"
else
    echo ""
    echo "❌ 오류가 발생했습니다. 오류 코드: $?"
fi

echo ""
