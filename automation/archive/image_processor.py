import os
import sys
from PIL import Image
from datetime import datetime

# ---------------------------------------------------------
# [경로 설정 로직]
# ---------------------------------------------------------
def get_desktop_path():
    """OneDrive 동기화 여부를 확인하여 실제 바탕화면 경로를 반환"""
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, "OneDrive", "바탕 화면"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "바탕 화면")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(home, "Desktop")

DESKTOP_PATH = get_desktop_path()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_IMG_ROOT = os.path.join(PROJECT_ROOT, "public", "static", "images")

# ---------------------------------------------------------
# [이미지 최적화 메인 함수]
# ---------------------------------------------------------
def run_image_optimization():
    # 1. 오늘 날짜 및 카테고리 설정
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")

    # [수석 책임자의 가이드] 인자가 있으면 사용, 없으면 'briefing'이 기본값
    category = sys.argv[1] if len(sys.argv) > 1 else "briefing"
    folder_name = f"{month_day}-{category}"

    # 2. 소스 및 타겟 경로 확정
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)
    target_dir = os.path.join(PROJECT_IMG_ROOT, year, folder_name)

    print(f"📍 인식된 바탕화면: {DESKTOP_PATH}")
    print(f"🔍 작업 카테고리: [{category.upper()}]")
    print(f"📂 소스 폴더: {source_dir}")
    print(f"📂 타겟 폴더: {target_dir}")

    if not os.path.exists(source_dir):
        print(f"❌ [에러] 바탕화면에 해당 폴더가 없습니다. ({folder_name})")
        return

    os.makedirs(target_dir, exist_ok=True)

    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    count = 0

    # 3. 이미지 변환 로직
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(valid_extensions):
            file_path = os.path.join(source_dir, filename)
            pure_name = os.path.splitext(filename)[0]
            target_path = os.path.join(target_dir, f"{pure_name}.webp")

            try:
                with Image.open(file_path) as img:
                    # 가로 1200px 최적화 (비율 유지)
                    if img.width > 1200:
                        ratio = 1200 / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)

                    img.save(target_path, "WEBP", quality=80)
                    print(f"✅ 변환 완료: {pure_name}.webp")
                    count += 1
            except Exception as e:
                print(f"❌ {filename} 처리 중 오류: {e}")

    print(f"\n✨ 성공: 총 {count}개의 이미지를 프로젝트로 배달했습니다.")

if __name__ == "__main__":
    run_image_optimization()