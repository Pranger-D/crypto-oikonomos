import os
import sys
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 1. 귀하가 만든 크롤러 함수 가져오기
from daily_news_crawler import get_morning_investment_briefing

# ---------------------------------------------------------
# 설정 (Settings & Init)
# ---------------------------------------------------------
# 환경 변수 로드 (.env)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)
# 글쓰기용 모델 (창의성/정리 능력 중요)
editor_model = genai.GenerativeModel("gemini-2.5-flash")

# 경로 설정
BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'blog')
PERSONAL_DIR = "G:/내 드라이브/News_Briefing"  # 소장용 경로

# ---------------------------------------------------------
# AI 에디터 함수 (HTML -> Engaging Blog Post)
# ---------------------------------------------------------
def rewrite_as_blog_post(html_content):
    print("✍️ [AI Editor] HTML 리포트를 바탕으로 매력적인 블로그 초안을 작성 중입니다...")
    
    prompt = f"""
    당신은 'Crypto Oikonomos' 블로그의 **수석 전문 에디터**입니다.
    아래 제공된 [HTML 리포트]는 팩트 위주의 딱딱한 데이터입니다.
    
    당신의 임무는 이 데이터를 바탕으로 **독자의 시선을 사로잡는(Hooking)**, 
    그리고 **정보 전달력이 뛰어난** 블로그 포스팅 초안(Markdown)을 작성하는 것입니다. 이모티콘은 쓰지마세요.

    [작성 원칙]
    1. **Role:** 금융/투자 전문 블로거 (전문적인 어투로, 그러나 이해하기 쉽게 설명해주세요.)
    2. **Hooking:** 서론에서 "왜 오늘 이 뉴스를 봐야 하는지" 강렬하게 어필하세요.
    3. **Structure:**
       - **🚀 오늘의 핵심 요약 (3줄)**: 바쁜 독자를 위해 맨 위에 배치.
       - **Section 1: 시장의 맥(Macro)**: 거시 경제 이슈를 스토리텔링으로 풀기.
       - **Section 2: 크립토 인사이트(Crypto)**: 단순 시세 나열 지양, 의미와 전망 위주.
       - **💡 투자자의 시선 (Conclusion)**: 마무리 제언.
    4. **Formatting:**
       - 가독성을 위해 **볼드체**, *이탤릭체*, > 인용구, - 리스트 등을 적극 활용하세요.
       - HTML 태그는 쓰지 말고, 오직 **Markdown 문법**만 사용하세요.
    5. **Constraint:** - 제공된 [HTML 리포트]에 없는 내용은 절대 지어내지 마십시오. (No Hallucination)
       - 분석이나 해석은 추가하되, 팩트는 유지하세요.

    [HTML 리포트 소스]
    {html_content}
    """

    try:
        response = editor_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ [AI Editor Error] 글 작성 중 오류 발생: {e}")
        return None

# ---------------------------------------------------------
# 메인 로직
# ---------------------------------------------------------
def save_to_blog():
    print("🚀 [System] 통합 브리핑 & 블로그 초안 생성 프로세스 시작...")

    # 1. 크롤러 실행 (데이터 수집)
    try:
        html_content = get_morning_investment_briefing()
        if not html_content:
            print("❌ [Error] HTML 내용이 비어있습니다. 중단합니다.")
            return
    except Exception as e:
        print(f"❌ [Error] 크롤러 실행 중 오류: {e}")
        return

    # 2. [소장용] HTML 파일 저장 (기존 방식 유지)
    try:
        save_folder = PERSONAL_DIR if os.path.exists(PERSONAL_DIR) else os.getcwd()
        html_filename = f"Briefing_{date.today()}.html"
        html_path = os.path.join(save_folder, html_filename)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✅ [Personal Copy] 소장용 리포트 저장 완료 ({html_path})")
    except Exception as e:
        print(f"⚠️ [Warning] 소장용 저장 실패: {e}")

    # 3. [블로그용] AI 에디팅 및 MDX 저장
    try:
        # (1) AI에게 글쓰기 시키기
        blog_body = rewrite_as_blog_post(html_content)
        
        if not blog_body:
            print("❌ 블로그 본문 생성 실패.")
            return

        # (2) 프론트매터(Frontmatter) 붙이기
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # 블로그에 표시될 요약문
        summary_text = "매일의 글로벌 암호화폐 인사이트 브리핑입니다."

        mdx_content = f"""---
title: '시장 브리핑: 오늘의 크립토 인사이트 ({today_str})'
date: '{today_str}'
tags: ['Macro', 'Crypto', 'Insight']
draft: true
summary: '{summary_text}'
---

{blog_body}
"""
        # (3) 파일 저장
        mdx_filename = f"{today_str}-briefing.mdx"
        mdx_path = os.path.join(BLOG_DIR, mdx_filename)

        with open(mdx_path, 'w', encoding='utf-8') as f:
            f.write(mdx_content)
        
        print(f"✅ [Blog Draft] 블로그 초안 생성 완료!")
        print(f"📂 위치: {mdx_path}")
        print("📝 [Next Step] Cursor에서 파일을 열어 내용을 검수하고 발행하세요.")

    except Exception as e:
        print(f"❌ [Error] 블로그 처리 중 오류: {e}")

if __name__ == "__main__":
    if not os.path.exists(BLOG_DIR):
        print(f"❌ [Config Error] 블로그 폴더({BLOG_DIR})를 찾을 수 없습니다.")
    else:
        save_to_blog()