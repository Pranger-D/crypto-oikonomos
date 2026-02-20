import os
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

FRED_API_KEY = os.getenv("FRED_API_KEY")

if not FRED_API_KEY:
    print("⚠️ FRED_API_KEY가 설정되지 않았습니다. .env 파일을 확인해 주세요.")

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "public" / "data"
DATA_FILE = DATA_DIR / "liquidity-data.json"

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# 재할인 창구(WDTGAL) 삭제됨
SERIES_MAP = {
    "SOFR": {"id": "SOFR"},
    "IORB": {"id": "IORB"},
    "TGA": {"id": "WTREGEN"},
    "RESERVES": {"id": "WRESBAL"},
    "SRF": {"id": "SRFTSYD"},
    "ON_RRP": {"id": "RRPONTSYD"},
    "TOTAL_ASSETS": {"id": "WALCL"} 
}

def fetch_fred_series(series_id, start_date):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc",
        "limit": 100000
    }
    
    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        result = {}
        if 'observations' in data:
            for obs in data['observations']:
                val = obs.get('value')
                # '.'은 FRED에서 데이터가 없는 날(휴일 등)을 의미함
                if val and val != '.':
                    result[obs.get('date')] = float(val)
        return result
    except Exception as e:
        print(f"❌ FRED '{series_id}' 데이터 수집 실패: {e}")
        return {}

def main():
    print(f"🔄 유동성 리스크 모니터 데이터 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not FRED_API_KEY:
        print("⚠️ 에러: FRED_API_KEY 누락. 스크립트를 종료합니다.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    
    existing_data = {"history": []}
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass

    history = existing_data.get("history", [])
    
    # 데이터가 10개(일) 미만이면 초기 세팅으로 간주하고 SRF 도입 시점부터 백필
    if len(history) < 10:
        start_date = "2021-07-28"
        print(f"📌 초기 백필 모드 (SRF 공식 도입일): {start_date} 부터 데이터를 수집합니다.")
        history = [] # 기존 불완전한 데이터가 있다면 초기화
    else:
        last_date = history[-1]["date"]
        # 마지막으로 확인된 날짜에서 넉넉하게 14일 전부터 가져옴
        start_date = (datetime.strptime(last_date, "%Y-%m-%d") - timedelta(days=14)).strftime("%Y-%m-%d")
        print(f"📌 일일 업데이트 모드: {start_date} 부터 최신 데이터를 수집합니다.")

    # 1. 지표별 데이터 수집
    raw_data = {}
    for key, info in SERIES_MAP.items():
        print(f"🔍 가져오는 중... {key} ({info['id']})")
        raw_data[key] = fetch_fred_series(info['id'], start_date)

    # 2. 수집된 범위의 모든 고유 날짜(영업일) 추출 후 정렬
    all_dates = set()
    for dates_dict in raw_data.values():
        all_dates.update(dates_dict.keys())
    sorted_dates = sorted(list(all_dates))
    
    # 3. 데이터 병합 (주간 데이터를 위해 전일 값으로 채우기 - Forward Fill)
    history_dict = {item['date']: item for item in history}
    
    # 이전 값을 기억하기 위한 변수 (최근 14일 업데이트 시, 그 이전 날짜가 있으면 가져옴)
    last_known = {}
    if history:
        for k in SERIES_MAP.keys():
            if k in history[-1]:
                last_known[k] = history[-1][k]

    for date in sorted_dates:
        if date not in history_dict:
            history_dict[date] = {"date": date}
            
        entry = history_dict[date]
        
        for key in SERIES_MAP.keys():
            if date in raw_data[key]:
                val = raw_data[key][date]
                if key == "TOTAL_ASSETS":
                    val = val / 1000.0  # 밀리언 -> 빌리언 스케일 변환
                entry[key] = val
                last_known[key] = val
            elif key in last_known:
                # 주간/월간 발표 지표(TGA, RESERVES 등)는 빈칸을 이전 값으로 연장선상에 그리기 위해 채움
                entry[key] = last_known[key]

        # 파생 지표 계산 (SOFR 역전 스프레드)
        if "SOFR" in entry and "IORB" in entry:
            entry["SPREAD_SOFR_IORB"] = round(entry["SOFR"] - entry["IORB"], 3)
            
    # 다시 리스트로 만들고 정렬
    updated_history = [history_dict[d] for d in sorted(history_dict.keys())]

    # 4. JSON 파일 저장 구조 다듬기 (헤더의 스냅샷용)
    latest_snapshot = {}
    if updated_history:
        last_entry = updated_history[-1]
        for k in SERIES_MAP.keys():
            if k in last_entry:
                latest_snapshot[k] = {"date": last_entry["date"], "value": last_entry[k]}
        if "SPREAD_SOFR_IORB" in last_entry:
            latest_snapshot["SPREAD_SOFR_IORB"] = {"date": last_entry["date"], "value": last_entry["SPREAD_SOFR_IORB"]}

    final_data = {
        "latest_snapshot": latest_snapshot,
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "history": updated_history
    }
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 데이터 저장 완료: {DATA_FILE} (총 {len(updated_history)}영업일 데이터)")
    except Exception as e:
        print(f"❌ 데이터 저장 중 오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
