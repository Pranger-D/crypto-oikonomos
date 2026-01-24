import os
import subprocess
import sys
from datetime import datetime

# ---------------------------------------------------------
# 설정 (Settings)
# ---------------------------------------------------------
# 프로젝트 루트 경로 (automation 폴더의 두 단계 위)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_command(command, cwd=PROJECT_ROOT):
    """터미널 명령어를 실행하고 결과를 출력하는 함수"""
    try:
        # 명령어 실행
        result = subprocess.run(
            command, 
            cwd=cwd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            encoding='utf-8' # 한글 깨짐 방지
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ [Error] 명령어 실행 실패: {command}")
        print(e.stderr)
        return False

def publish_to_github():
    print("🚀 [System] 블로그 배포 자동화를 시작합니다...")
    
    # 1. 변경사항 확인 (Git Status)
    print("\n🔍 [Step 1] 변경사항 확인 중...")
    if not run_command("git status"):
        return

    # 2. 사용자 확인 (안전장치)
    confirm = input("👉 정말로 배포(Publish) 하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("🚫 배포가 취소되었습니다.")
        return

    # 3. Git Add
    print("\n📦 [Step 2] 변경사항 담기 (git add)...")
    if not run_command("git add ."):
        return

    # 4. Git Commit
    # 커밋 메시지에 자동으로 날짜/시간을 넣어줍니다.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Blog Update: {timestamp} (Auto-deployed via Python)"
    
    print(f"\n📝 [Step 3] 커밋 작성 (git commit): '{commit_message}'")
    if not run_command(f'git commit -m "{commit_message}"'):
        return

    # 5. Git Push
    print("\nairplane [Step 4] 깃허브로 발사 (git push)...")
    if run_command("git push origin main"):
        print("\n✅ [Success] 배포 성공! 잠시 후 Vercel이 사이트를 업데이트합니다.")
        print("🌍 내 블로그: https://crypto-oikonomos.vercel.app")
    else:
        print("\n❌ [Fail] 배포 실패. 로그를 확인해주세요.")

if __name__ == "__main__":
    publish_to_github()