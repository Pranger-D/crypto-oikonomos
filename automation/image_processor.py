import os
from PIL import Image
from datetime import datetime

# [경로 설정]
# 1. 바탕화면 경로
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
# 2. 프로젝트 이미지 루트 (automation 폴더 기준 두 단계 위 -> public/static/images)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_IMG_ROOT = os.path.join(PROJECT_ROOT, "public", "static", "images")


def run_image_optimization():
    # 오늘 날짜 정보 추출
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")

    # 폴더명 규칙 (브리핑용 고정)
    folder_name = f"{month_day}-briefing"

    # 소스 및 타겟 경로 확정
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)
    target_dir = os.path.join(PROJECT_IMG_ROOT, year, folder_name)

    print(f"🔍 작업 시작...")
    print(f"📂 소스: {source_dir}")
    print(f"📂 타겟: {target_dir}")

    if not os.path.exists(source_dir):
        print(f"❌ [에러] 바탕화면에 해당 날짜 폴더가 없습니다. 경로를 확인하세요.")
        return

    os.makedirs(target_dir, exist_ok=True)

    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    count = 0

    for filename in os.listdir(source_dir):
        if filename.lower().endswith(valid_extensions):
            file_path = os.path.join(source_dir, filename)

            # 원본명 유지 + webp 확장자
            pure_name = os.path.splitext(filename)[0]
            target_path = os.path.join(target_dir, f"{pure_name}.webp")

            try:
                with Image.open(file_path) as img:
                    # 가로 1200px 최적화
                    if img.width > 1200:
                        ratio = 1200 / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)

                    img.save(target_path, "WEBP", quality=80)
                    print(f"✅ 처리 완료: {pure_name}.webp")
                    count += 1
            except Exception as e:
                print(f"❌ {filename} 처리 실패: {e}")

    print(f"\n✨ 총 {count}개의 이미지가 최적화되어 프로젝트에 반영되었습니다.")


if __name__ == "__main__":
    run_image_optimization()
