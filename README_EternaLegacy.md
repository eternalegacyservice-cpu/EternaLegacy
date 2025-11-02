# EternaLegacy Git Security Kit (Cross‑Platform)

이 패키지는 **Windows / macOS / Linux** 어디서나 동일하게 동작하는 *보안 Git 자동 설정* 스크립트입니다.
루트 폴더(예: `EternaLegacy/`)에서 실행하면, 다음을 자동으로 구성합니다.

- `.gitignore` : 민감 파일 및 불필요 캐시 제외 (**EternaLegacy 구조에 최적화**)
- `.pre-commit-config.yaml` : `detect-secrets` 기반 커밋 사전 시크릿 검사
- `.secrets.baseline` : 최초 스캔 결과
- `.git/hooks/pre-push` : 기본 **푸시 차단**, `ALLOW_PUSH=1` 일시 허용
- Python 가상환경 `.venv` 생성 및 의존성 설치

## 설치/실행

### Windows (PowerShell)
```powershell
# 1) EternaLegacy 루트로 이동
cd "C:\...\EternaLegacy"

# 2) 보안 스크립트 압축 해제 후 아래 실행
powershell -ExecutionPolicy Bypass -File .\setup_secure_git.ps1
