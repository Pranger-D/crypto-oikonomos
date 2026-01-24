import os
from datetime import datetime
from markdownify import markdownify as md

# ==========================================
# 1. 설정 (Settings)
# ==========================================
# 블로그 글이 저장될 위치 (automation 폴더에서 두 단계 위 -> data -> blog)
BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'blog')

# ==========================================
# 2. 가상의 HTML 데이터 (나중엔 귀하의 코드가 만든 파일 내용을 읽어올 것임)
# ==========================================
raw_html = """
<h1>2026년 1월 24일 경제 브리핑</h1>
<p>오늘은 <strong>환율</strong>이 소폭 하락했습니다.</p>
<ul>
    <li>달러/원: 1350원</li>
    <li>비트코인: 상승세 유지</li>
</ul>
<p>시장 관망세가 지속되고 있습니다.</p>
"""

# ==========================================
# 3. 변환 로직 (HTML -> MDX with Frontmatter)
# ==========================================
def create_blog_post(html_content):
    # (1) 오늘 날짜 구하기
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # (2) HTML을 마크다운으로 변환
    markdown_body = md(html_content)

    # (3) 블로그용 머리말(Frontmatter) 작성
    # Next.js 블로그는 이 머리말이 꼭 있어야 글을 인식합니다.
    blog_post = f"""---
title: '자동 생성된 경제 리포트 ({today_str})'
date: '{today_str}'
tags: ['Economy', 'Automation', 'Test']
draft: false
summary: 'Python 봇이 자동으로 변환하여 발행한 리포트입니다.'
---

{markdown_body}
"""
    
    # (4) 파일 저장
    # 파일명: 2026-01-23-report.mdx
    filename = f"{today_str}-report.mdx"
    file_path = os.path.join(BLOG_DIR, filename)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(blog_post)

    print(f"✅ 성공! 파일이 생성되었습니다: {file_path}")

# ==========================================
# 4. 실행
# ==========================================
if __name__ == "__main__":
    # 블로그 폴더가 진짜 있는지 확인
    if not os.path.exists(BLOG_DIR):
        print(f"❌ 오류: 블로그 폴더를 찾을 수 없습니다: {BLOG_DIR}")
    else:
        create_blog_post(raw_html)