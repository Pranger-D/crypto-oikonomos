import os
import io
import math
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

# ==========================================
# 1. 설정 및 디자인 테마
# ==========================================

def get_desktop_path():
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "바탕 화면"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "바탕 화면")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(home, "Desktop")

DESKTOP_PATH = get_desktop_path()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_IMG_ROOT = os.path.join(PROJECT_ROOT, "public", "static", "images")

def apply_light_theme():
    plt.style.use('default')
    plt.rcParams.update({
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#f8f9fa",
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

def download_data(ticker_symbol, days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker_symbol, start=start_date.strftime("%Y-%m-%d"), end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"))
    
    if df.empty:
        return None
        
    df.index = df.index.tz_localize(None)
    
    # squeeze 처리
    close_series = df['Close']
    if hasattr(close_series, 'columns'): # 다중 티커 혹은 특수 구조 대비
        if ticker_symbol in close_series.columns:
            close_series = close_series[ticker_symbol]
        else:
             close_series = close_series.iloc[:, 0]
             
    return df, close_series

# ==========================================
# 2. 차트 템플릿 엔진 (다양화)
# ==========================================

# 2.1 Asset Performance (기본 등락 선차트)
def render_asset_performance(ticker_symbol, title, days=14):
    apply_light_theme()
    data = download_data(ticker_symbol, days)
    if not data: return None
    _, close_series = data
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    line_color = "#005a9c" 
    
    ax.plot(close_series.index, close_series.values, color=line_color, linewidth=2.5, label=ticker_symbol)
    ax.fill_between(close_series.index, close_series.values, min(close_series.values)*0.99, color=line_color, alpha=0.05)
    
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.grid(True, zorder=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # 마지막 날 마킹
    last_price = close_series.iloc[-1]
    last_date = close_series.index[-1]
    first_price = close_series.iloc[0]
    pct_change = ((last_price - first_price) / first_price) * 100
    
    color_change = "#28a745" if pct_change >= 0 else "#dc3545"
    sign = "+" if pct_change >= 0 else ""
    
    ax.scatter([last_date], [last_price], color=color_change, s=80, zorder=5)
    ax.annotate(f"{sign}{pct_change:.1f}%\n(${last_price:,.0f})", 
                xy=(last_date, last_price), xytext=(10, 0),
                textcoords="offset points", va="center", ha="left",
                fontsize=11, fontweight="bold", color=color_change,
                bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec=color_change, alpha=0.9))

    plt.tight_layout()
    return fig

# 2.2 Macro Compare (상대 수익률 0선 비교)
def render_macro_compare(ticker1, ticker2, alias1, alias2, title, days=30):
    apply_light_theme()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")    
    df = yf.download(f"{ticker1} {ticker2}", start=start_date)
    
    if df.empty: return None
    close_df = df['Close']
    
    normalized_df = (close_df / close_df.iloc[0] - 1) * 100
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    color1 = "#f7931a"
    color2 = "#34495e"
    
    ax.plot(normalized_df.index, normalized_df[ticker1], color=color1, linewidth=2.5, label=alias1)
    ax.plot(normalized_df.index, normalized_df[ticker2], color=color2, linewidth=2.5, label=alias2)
    ax.axhline(0, color="#95a5a6", linewidth=1.5, linestyle="--", zorder=1)
    
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("Return (%)", fontweight="bold")
    ax.legend(loc="upper left", frameon=False, fontsize=12)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    
    plt.tight_layout()
    return fig

# 2.3 Moving Average (이동 평균 선: 최근 장기 트렌드)
def render_moving_average(ticker_symbol, title, days=90):
    apply_light_theme()
    # MA를 계산하려면 과거 데이터가 더 필요함
    data_days = days + 60
    data = download_data(ticker_symbol, data_days)
    if not data: return None
    _, close_series = data
    
    ma_20 = close_series.rolling(window=20).mean()
    ma_50 = close_series.rolling(window=50).mean()
    
    # 화면에 보여줄 기간 자르기 (요청받은 days 만큼만)
    cut = -days
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    ax.plot(close_series.index[cut:], close_series.values[cut:], color="#2c3e50", linewidth=1.5, label="Price", alpha=0.8)
    ax.plot(ma_20.index[cut:], ma_20.values[cut:], color="#e74c3c", linewidth=2.0, label="20-Day MA")
    ax.plot(ma_50.index[cut:], ma_50.values[cut:], color="#3498db", linewidth=2.0, label="50-Day MA")
    
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.legend(loc="upper left", frameon=False, fontsize=11)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    plt.tight_layout()
    return fig

# 2.4 Volatility (일일 변동폭 바 차트)
def render_volatility(ticker_symbol, title, days=30):
    apply_light_theme()
    data = download_data(ticker_symbol, days)
    if not data: return None
    _, close_series = data
    
    daily_returns = close_series.pct_change() * 100
    daily_returns = daily_returns.dropna()
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    # 양수는 초록 막대, 음수는 빨간 막대
    colors = ["#28a745" if val >= 0 else "#dc3545" for val in daily_returns.values]
    
    bars = ax.bar(daily_returns.index, daily_returns.values, color=colors, width=0.6, alpha=0.85)
    
    ax.axhline(0, color="#333", linewidth=1, linestyle="-", zorder=2) # 0 기준선
    
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("Daily Volatility (%)", fontweight="bold")
    ax.grid(True, axis='y') # Y축 그물망만
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//6)))
    
    y_max = max(abs(daily_returns.min()), abs(daily_returns.max()))
    ax.set_ylim(-math.ceil(y_max)-1, math.ceil(y_max)+1)
    
    plt.tight_layout()
    return fig


# ==========================================
# 3. 브릿지 API (메인에서 호출)
# ==========================================
def generate_and_save_chart(chart_instruction, category="briefing", target_date=None):
    print(f"🎨 [Chart Maker V3] AI 지시서 접수: {chart_instruction}")
    
    ctype = chart_instruction.get("type", "asset")
    title = chart_instruction.get("title", "Market View")
    
    fig = None
    if ctype == "asset":
        ticker = chart_instruction.get("ticker", "BTC-USD")
        fig = render_asset_performance(ticker, title, days=14)
    elif ctype == "compare":
        tickers = chart_instruction.get("tickers", ["BTC-USD", "^IXIC"])
        aliases = chart_instruction.get("aliases", ["Bitcoin", "NASDAQ"])
        fig = render_macro_compare(tickers[0], tickers[1], aliases[0], aliases[1], title, days=30)
    elif ctype == "ma":
        ticker = chart_instruction.get("ticker", "BTC-USD")
        fig = render_moving_average(ticker, title, days=60)
    elif ctype == "volatility":
        ticker = chart_instruction.get("ticker", "BTC-USD")
        fig = render_volatility(ticker, title, days=30)
    else:
        # fallback
        ticker = chart_instruction.get("ticker", "BTC-USD")
        fig = render_asset_performance(ticker, title, days=14)
    
    if not fig:
        print("❌ 차트 생성 실패")
        return None
        
    if target_date:
        now = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        now = datetime.now()
        
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    folder_name = f"{month_day}-{category}"
    
    target_dir = os.path.join(PROJECT_IMG_ROOT, year, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"dynamic_chart_{month_day}.webp"
    file_path = os.path.join(target_dir, filename)
    
    fig.savefig(file_path, format="webp", bbox_inches="tight", dpi=150)
    plt.close(fig)
    
    print(f"✅ [Chart Maker] 차트 생성 완료: {file_path}")
    mdx_image_path = f"/static/images/{year}/{folder_name}/{filename}"
    return mdx_image_path

if __name__ == "__main__":
    inst = {
        "type": "ma",  # test moving average
        "ticker": "BTC-USD",
        "title": "Bitcoin Moving Average Support"
    }
    generate_and_save_chart(inst)
