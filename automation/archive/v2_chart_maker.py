import os
import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

# ==========================================
# 1. 설정 및 디자인 테마
# ==========================================

# 저장 경로 셋업 (image_processor.py 로직 계승)
def get_desktop_path():
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

# [Light Theme] Bloomberg / WSJ 깔끔한 스타일
def apply_light_theme():
    plt.style.use('default')
    plt.rcParams.update({
        "figure.facecolor": "#ffffff",  # 완전 흰색 배경
        "axes.facecolor": "#f8f9fa",    # 살짝 밝은 회색 계열 (차트 내부)
        "axes.edgecolor": "#e0e0e0",
        "axes.labelcolor": "#333333",
        "xtick.color": "#555555",
        "ytick.color": "#555555",
        "text.color": "#2c3e50",
        "font.family": "sans-serif",
        "font.size": 11,
        "grid.color": "#ebebeb",
        "grid.linestyle": "-",
        "grid.linewidth": 1.0,
        "grid.alpha": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

# ==========================================
# 2. 차트 템플릿 엔진
# ==========================================

def render_asset_performance(ticker_symbol, title, days=14):
    """
    단일 자산의 성과를 보여주는 깔끔한 선 차트 (예: 최근 14일 비트코인 랠리)
    """
    apply_light_theme()
    
    # 1. 데이터 다운로드
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker_symbol, start=start_date.strftime("%Y-%m-%d"), end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"))
    
    if df.empty:
        print(f"⚠️ [Chart] {ticker_symbol} 데이터를 불러오지 못했습니다.")
        return None

    # 시계열 데이터 정리
    df.index = df.index.tz_localize(None)
    
    # 2. 그리기
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150) # 고해상도, 와이드 비율
    
    # 종가 라인 (Bloomberg 스타일 진한 파란색)
    line_color = "#005a9c" 
    
    # squeeze 처리 (다중 티커 방지용)
    if isinstance(df['Close'], type(df)):
        close_series = df['Close'][ticker_symbol]
    else:
        close_series = df['Close']
        
    ax.plot(close_series.index, close_series.values, color=line_color, linewidth=2.5, label=ticker_symbol)
    
    # 차트 하단 그라데이션(알파) 효과
    ax.fill_between(close_series.index, close_series.values, min(close_series.values)*0.99, color=line_color, alpha=0.05)
    
    # 3. 꾸미기
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.grid(True, zorder=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    
    # Y축 포맷 (천단위 콤마)
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # 마지막 날 가격 마킹 (강조 포인트)
    last_price = close_series.iloc[-1]
    last_date = close_series.index[-1]
    
    # 시작가 대비 등락률 마킹
    first_price = close_series.iloc[0]
    pct_change = ((last_price - first_price) / first_price) * 100
    color_change = "#28a745" if pct_change >= 0 else "#dc3545" # 초록/빨강
    sign = "+" if pct_change >= 0 else ""
    
    ax.scatter([last_date], [last_price], color=color_change, s=80, zorder=5)
    ax.annotate(f"{sign}{pct_change:.1f}%\n(${last_price:,.0f})", 
                xy=(last_date, last_price), xytext=(10, 0),
                textcoords="offset points", va="center", ha="left",
                fontsize=11, fontweight="bold", color=color_change,
                bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec=color_change, alpha=0.9))

    plt.tight_layout()
    return fig

def render_macro_compare(ticker1, ticker2, alias1, alias2, title, days=30):
    """
    두 자산의 상대적 퍼포먼스(수익률%)를 0선 기준으로 비교하는 차트
    예: 비트코인 vs 나스닥 한달 비교
    """
    apply_light_theme()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")    
    df = yf.download(f"{ticker1} {ticker2}", start=start_date)
    
    if df.empty:
         return None
         
    close_df = df['Close']
    
    # 시작일을 0%로 맞추어 누적 수익률 계산
    normalized_df = (close_df / close_df.iloc[0] - 1) * 100
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    color1 = "#f7931a" # 비트코인 주황
    color2 = "#34495e" # 나스닥 다크블루
    
    # 선 그리기
    ax.plot(normalized_df.index, normalized_df[ticker1], color=color1, linewidth=2.5, label=alias1)
    ax.plot(normalized_df.index, normalized_df[ticker2], color=color2, linewidth=2.5, label=alias2)
    
    # 0% 기준선 강조
    ax.axhline(0, color="#95a5a6", linewidth=1.5, linestyle="--", zorder=1)
    
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("Return (%)", fontweight="bold")
    ax.legend(loc="upper left", frameon=False, fontsize=12)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    
    plt.tight_layout()
    return fig

# ==========================================
# 3. 브릿지 API (메인에서 호출하는 함수)
# ==========================================

def generate_and_save_chart(chart_instruction, category="briefing"):
    """
    AI가 떨어뜨린 JSON 지시서(chart_instruction)를 받아 차트를 그리고,
    프로젝트 폴더(public/static/images)에 webp로 최종 저장합니다.
    """
    print(f"🎨 [Chart Maker] AI 지시서 접수: {chart_instruction}")
    
    ctype = chart_instruction.get("type", "asset")
    title = chart_instruction.get("title", "Market Trend")
    
    fig = None
    if ctype == "asset":
        ticker = chart_instruction.get("ticker", "BTC-USD")
        fig = render_asset_performance(ticker, title, days=14)
    elif ctype == "compare":
        tickers = chart_instruction.get("tickers", ["BTC-USD", "^IXIC"])
        aliases = chart_instruction.get("aliases", ["Bitcoin", "NASDAQ"])
        fig = render_macro_compare(tickers[0], tickers[1], aliases[0], aliases[1], title, days=30)
    
    if not fig:
        print("❌ 차트 생성 실패")
        return None
        
    # 저장 경로 계산
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    folder_name = f"{month_day}-{category}"
    
    # 타겟 디렉토리
    target_dir = os.path.join(PROJECT_IMG_ROOT, year, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"dynamic_chart_{month_day}.webp"
    file_path = os.path.join(target_dir, filename)
    
    # WebP로 저장
    fig.savefig(file_path, format="webp", bbox_inches="tight", dpi=150)
    plt.close(fig)
    
    print(f"✅ [Chart Maker] 동적 차트 생성 완료: {file_path}")
    
    # MDX에 삽입될 경로는 public 밑줄 경로부터
    mdx_image_path = f"/static/images/{year}/{folder_name}/{filename}"
    return mdx_image_path

if __name__ == "__main__":
    # Test
    inst = {
        "type": "asset",
        "ticker": "BTC-USD",
        "title": "Bitcoin 14-Day Surge After Rate Cut Hints"
    }
    generate_and_save_chart(inst)
