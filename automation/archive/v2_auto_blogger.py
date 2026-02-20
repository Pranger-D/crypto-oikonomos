import os
import sys
import json
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# V2 모듈 임포트
from v2_news_brain import build_brain_data
from v2_chart_maker import generate_and_save_chart

# ==========================================
# 1. 환경 설정
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")

genai.configure(api_key=GOOGLE_API_KEY)
editor_model = genai.GenerativeModel("gemini-2.5-flash")

# 경로 설정
BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "blog")
PERSONAL_DIR = "G:/내 드라이브/News_Briefing"

# ==========================================
# 2. 메인 글쓰기 & 차트 주문 (AI 2차 프롬프트)
# ==========================================
def generate_blog_content_and_chart_instruction(brain_data):
    print("✍️ [AI Editor] 수집된 브레인 데이터(Context & VIP News)를 바탕으로 블로그 포스팅 초안 작성 중...")
    
    # 전달할 컨텍스트 데이터 형태 잡기 
    context_str = json.dumps(brain_data["context"], ensure_ascii=False, indent=2)
    vip_news_str = json.dumps(brain_data["vip_news"], ensure_ascii=False, indent=2)

    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""
    당신은 'Crypto Oikonomos' 블로그의 **수석 전문 에디터**입니다.
    오늘 날짜는 {today_str} 입니다.
    
    아래에는 두 가지 데이터가 제공됩니다.
    1. [Macro Context]: 최근 연준, 기관들의 주요 거시 경제 리포트 핵심입니다. (이 흐름 위에서 시장을 해석하세요)
    2. [VIP News]: 오늘 시장을 뒤흔든 진정한 핵심 뉴스 딱 5개입니다.
    
    [작성 원칙]
    1. **Role:** 매크로와 크립토를 연결(Connect the dots)하는 뛰어난 통찰력의 블로거.
    2. **Hooking:** 서론에서 "오늘 왜 이 포스팅을 반드시 읽어야 하는지" 독자의 시선을 사로잡으세요.
    3. **Structure (Markdown):**
       - **🚀 오늘의 핵심 요약 (3줄)**
       - **1. 시장의 맥 (Macro Insights)**: [Macro Context]와 관련 뉴스를 결합하여 서술.
       - **2. 크립토 다이내믹스 (Crypto Moves)**: [VIP News]의 크립토/온체인 이슈를 해석. (각 뉴스 끝에 링크 표기)
       - **3. 에디터의 시선 (Conclusion)**: 마무리 제언 (지나친 확언은 피하고 균형감 있게).
    4. **Tone & Formatting:** 번잡한 이모티콘은 최소화하고, 볼드체와 인용구(>)를 적절히 써서 전문적이고 깔끔하게.
    5. **Image Placeholder**: 본문 중 차트가 들어가면 딱 좋을 시각적 포인트(예: 매크로 설명 직후 또는 마무리 전) 한 곳에 반드시 `[CHART_PLACEHOLDER]` 라는 텍스트를 정회하게 1번만 삽입하세요.

    [Chart Instruction 추가 미션]
    블로그 내용과 가장 잘 어울리는 동적 차트(파이썬이 그릴 것)에 대한 지시서를 마크다운 코드블록 가장 하단에 작성해 주세요.
    - `type`: "asset" (단일 자산 등락) 또는 "compare" (두 자산 비교)
    - `ticker`: "BTC-USD", "^IXIC"(나스닥) 등 Yahoo Finance 티커 기호
    
    [데이터 소스]
    # Macro Context:
    {context_str}
    
    # VIP News (Today):
    {vip_news_str}
    
    [출력 포맷 엄수]
    (블로그 포스팅 본문 마크다운으로 쭉 작성...)
    [CHART_PLACEHOLDER]
    (남은 본문 작성...)
    
    ---JSON_START---
    {{
      "type": "asset",
      "ticker": "BTC-USD",
      "title": "Bitcoin Recent Movement"
    }}
    ---JSON_END---
    """
    
    try:
        response = editor_model.generate_content(prompt)
        text = response.text
        
        # 본문과 JSON 지시서 분리
        if "---JSON_START---" in text and "---JSON_END---" in text:
            parts = text.split("---JSON_START---")
            blog_body = parts[0].strip()
            json_str = parts[1].split("---JSON_END---")[0].strip()
            # 마크다운 찌꺼기 제거
            if json_str.startswith("```json"): json_str = json_str[7:]
            if json_str.endswith("```"): json_str = json_str[:-3]
            
            try:
                 chart_instruction = json.loads(json_str)
            except:
                 chart_instruction = {"type": "asset", "ticker": "BTC-USD", "title": "Bitcoin Daily Trend"}
        else:
            blog_body = text
            chart_instruction = {"type": "asset", "ticker": "BTC-USD", "title": "Bitcoin Daily Trend"}
            
        return blog_body, chart_instruction
    except Exception as e:
        print(f"❌ [AI Editor Error] 글 작성 중 오류 발생: {e}")
        return None, None

# ==========================================
# 3. 메인 자동화 로직
# ==========================================
def run_v2_automation():
    print("\n🚀 [V2 Auto Blogger] 혁신적인 완전 자동화 파이프라인을 시작합니다...\n")
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    category = sys.argv[1] if len(sys.argv) > 1 else "briefing"
    
    # 1. 브레인 가동 (컨텍스트 + VIP 뉴스 필터링)
    brain_data = build_brain_data()
    if not brain_data.get("vip_news"):
         print("❌ 수집된 VIP 뉴스가 없어 중단합니다.")
         return
         
    # 2. 블로그 작성 & 차트 오더
    blog_body, chart_instruction = generate_blog_content_and_chart_instruction(brain_data)
    
    if not blog_body:
         return
    
    # 3. 차트 생성공장에 오더 전달
    mdx_image_path = generate_and_save_chart(chart_instruction, category=category)
    
    # 4. 블로그 본문에 차트 이미지 끼워넣기 (플레이스홀더 교체)
    image_markdown = f"\n<div className=\"flex justify-center my-8\">\n  <img src=\"{mdx_image_path}\" alt=\"{chart_instruction.get('title')}\" className=\"rounded-lg shadow-lg border border-gray-200\" />\n</div>\n"
    if "[CHART_PLACEHOLDER]" in blog_body:
         blog_body = blog_body.replace("[CHART_PLACEHOLDER]", image_markdown)
    else: # 없으면 맨 뒤에 추가
         blog_body += image_markdown
    
    # 5. Frontmatter 조립
    summary_text = f"오늘의 글로벌 암호화폐 인사이트 브리핑입니다."
    
    mdx_content = f"""---
title: '시장 브리핑: 오늘의 크립토 브리핑 ({today_str})'
date: '{today_str}'
tags: ['{category.capitalize()}', 'Bitcoin', 'Fed', 'Macro']
draft: true
summary: '{summary_text}'
---

{blog_body}

---
_Disclaimer: 이 보고서는 제공된 데이터에 기반한 분석이며, 투자 조언을 목적으로 하지 않습니다._
"""
    # 6. 파일 저장
    mdx_content = mdx_content.replace("$", "\\$")
    mdx_filename = f"{today_str}-{category}.mdx" 
    mdx_path = os.path.join(BLOG_DIR, mdx_filename)

    with open(mdx_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    print(f"\n✅ [Target Reached] V2 블로그 자동 생성 완료!")
    print(f"📄 저장 경로: {mdx_path}")
    print(f"📊 저장된 차트: {mdx_image_path}")

if __name__ == "__main__":
    run_v2_automation()
