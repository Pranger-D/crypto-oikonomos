"""
dashboard-data.json의 모든 NaN 값을 null로 완전히 변환
- 정규식 사용하여 모든 패턴 처리
"""

import json
import re
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("🔧 dashboard-data.json NaN 완전 제거")
print("=" * 60)

# 파일 읽기
print(f"\n📂 파일 로드 중...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# NaN 개수 확인
nan_count = content.count('NaN')
print(f"✅ 파일 로드 완료")
print(f"   발견된 NaN: {nan_count}개")

if nan_count > 0:
    print(f"\n🔄 모든 NaN → null 변환 중...")
    
    # 모든 가능한 NaN 패턴 처리
    patterns = [
        (r': NaN,', ': null,'),
        (r': NaN}', ': null}'),
        (r': NaN\s', ': null '),
        (r': NaN\n', ': null\n'),
        (r': NaN\r', ': null\r'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # 파일 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 재확인
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        new_content = f.read()
    
    remaining_nan = new_content.count('NaN')
    
    print(f"✅ 변환 완료:")
    print(f"   - 제거된 NaN: {nan_count}개")
    print(f"   - 남은 NaN: {remaining_nan}개")
    
    if remaining_nan > 0:
        print(f"\n⚠️ 경고: {remaining_nan}개 NaN이 여전히 남아있습니다.")
        # NaN 위치 찾기
        positions = [m.start() for m in re.finditer(r'NaN', new_content)]
        for pos in positions[:5]:
            start = max(0, pos - 50)
            end = min(len(new_content), pos + 50)
            print(f"\n   위치 {pos}: ...{new_content[start:end]}...")
    
    # JSON 검증
    print(f"\n🔍 JSON 유효성 검증 중...")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ JSON 유효성 검증 통과!")
        
        file_size = DATA_FILE.stat().st_size / 1024
        print(f"\n📦 파일 크기: {file_size:.1f} KB")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"   위치: line {e.lineno}, column {e.colno}")
        exit(1)
else:
    print(f"\nℹ️ NaN 값이 없습니다.")

print(f"\n🎉 수정 완료! 브라우저 새로고침 해주세요.")
