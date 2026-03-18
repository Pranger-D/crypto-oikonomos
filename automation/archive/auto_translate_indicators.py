"""
거시지표 자동 번역 시스템
- 새로운 지표 발견 시 Gemini API로 번역
- 번역 결과를 JSON 파일에 저장
- 다음부터는 저장된 번역 재사용
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY가 없습니다.")
    exit(1)

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"
TRANSLATION_FILE = Path(__file__).parent / "indicator_translations.json"

print("🔄 거시지표 자동 번역 시스템")
print("=" * 60)

# 기존 번역 로드
if TRANSLATION_FILE.exists():
    with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
        translations = json.load(f)
    print(f"✅ 기존 번역 로드: {len(translations)}개")
else:
    translations = {}
    print("📝 새 번역 파일 생성")

# 데이터에서 모든 지표 수집
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_indicators = set()
for indicators in data['macroIndicators'].values():
    for ind in indicators:
        # 월/분기 정보 제거 (정규식 수정)
        import re
        base_indicator = re.sub(r'\s+\([A-Za-z0-9]+\)\s*$', '', ind['indicator']).strip()
        all_indicators.add(base_indicator)

print(f"\n📊 발견된 지표: {len(all_indicators)}개")

# 번역이 필요한 지표 찾기
need_translation = [ind for ind in all_indicators if ind not in translations]

if not need_translation:
    print("\n✅ 모든 지표가 이미 번역되어 있습니다!")
else:
    print(f"\n🔄 번역 필요: {len(need_translation)}개")
    print("\n번역 중...")
    
    for idx, indicator in enumerate(need_translation, 1):
        print(f"  [{idx}/{len(need_translation)}] {indicator[:40]}...", end=" ")
        
        try:
            prompt = f"""경제 지표 이름을 한글로 번역하세요.

지표: "{indicator}"

규칙:
- 경제/금융 전문 용어로 정확히 번역
- 약어는 괄호 포함: CPI → 소비자물가지수(CPI)
- 고유명사는 유지: ISM, S&P, ADP, FOMC, JOLTS
- 번역만 출력 (다른 설명 없이)

예:
"CPI" → "소비자물가지수(CPI)"
"ISM Manufacturing PMI" → "ISM 제조업 PMI"
"Initial Jobless Claims" → "신규 실업수당 청구"

번역:"""
            
            response = model.generate_content(prompt)
            translation = response.text.strip().strip('"').strip("'")
            
            # 번역 저장
            translations[indicator] = translation
            print(f"✅ {translation[:40]}")
            
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            # 오류 시 원문 사용
            translations[indicator] = indicator

# 번역 파일 저장
with open(TRANSLATION_FILE, "w", encoding="utf-8") as f:
    json.dump(translations, f, ensure_ascii=False, indent=2)

print(f"\n💾 번역 파일 저장 완료: {TRANSLATION_FILE}")
print(f"📊 총 번역: {len(translations)}개")

# TypeScript 파일 생성
print(f"\n🔄 TypeScript 번역 파일 생성 중...")

ts_content = """// 자동 생성된 거시지표 번역 파일
// 수정하지 마세요. indicator_translations.json을 수정하고 스크립트를 다시 실행하세요.

export const indicatorTranslations: Record<string, string> = {
"""

for indicator, translation in sorted(translations.items()):
    # 특수문자 이스케이프
    escaped_indicator = indicator.replace("'", "\\'").replace('"', '\\"')
    escaped_translation = translation.replace("'", "\\'").replace('"', '\\"')
    ts_content += f"    '{escaped_indicator}': '{escaped_translation}',\n"

ts_content += "}\n"

ts_file = PROJECT_ROOT / "components" / "Dashboard" / "indicatorTranslations.ts"
with open(ts_file, "w", encoding="utf-8") as f:
    f.write(ts_content)

print(f"✅ TypeScript 파일 생성: {ts_file}")

print(f"\n🎉 자동 번역 완료!")
print(f"\n💡 다음 단계:")
print(f"   1. MacroIndicators.tsx에서 import 추가")
print(f"   2. 번역 확인 후 커밋")
