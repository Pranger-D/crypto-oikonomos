import { ReactNode } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import Link from '@/components/Link'
import PageTitle from '@/components/PageTitle'
import SectionContainer from '@/components/SectionContainer'
import Image from '@/components/Image'
import siteMetadata from '@/data/siteMetadata'
import ScrollTopAndComment from '@/components/ScrollTopAndComment'
import ScrollProgressBar from '@/components/ScrollProgressBar' // 방금 만든 컴포넌트
import { formatDate } from 'pliny/utils/formatDate'

// 사이드바 데이터 처리를 위한 임포트
import { allBlogs } from 'contentlayer/generated'
import { sortPosts } from 'pliny/utils/contentlayer'

interface LayoutProps {
  content: CoreContent<Blog>
  authorDetails: CoreContent<Authors>[]
  next?: { path: string; title: string }
  prev?: { path: string; title: string }
  children: ReactNode
}

export default function PostLayout({ content, next, prev, children }: LayoutProps) {
  const { date, title, tags, slug } = content

  // 1. 사이드바용 데이터 필터링 로직
  // 'Briefing', 'Insight', 'Study' 태그가 달린 최신 글을 각각 3개씩 가져옵니다.
  const sortedPosts = sortPosts(allBlogs)
  const targetCategories = ['Briefing', 'Insight', 'Study']
  
  return (
    // 전체 배경: 아주 밝은 회색 (레퍼런스 느낌)
    <div className="bg-[#F9FAFB] min-h-screen">
      
      {/* 1. 상단 진행률 표시줄 (스크롤 시 차오름) */}
      <ScrollProgressBar />

      <SectionContainer>
        <ScrollTopAndComment />
        
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 xl:grid xl:grid-cols-12 xl:gap-x-12 xl:px-0">
          
          {/* =========================================
              [Left Column] 메인 콘텐츠 영역 (8칸 차지)
          ========================================= */}
          <div className="xl:col-span-8">
            <article>
              {/* (1) 헤더 영역: 제목 -> 구분선 */}
              <header className="mb-8 space-y-4">
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-500">
                    <time dateTime={date}>
                      {formatDate(date, siteMetadata.locale)}
                    </time>
                  </div>
                  <PageTitle>{title}</PageTitle>
                </div>
                {/* 구분선: 배경보다 살짝 어두운 회색 */}
                <div className="h-[1px] w-full bg-gray-300" />
              </header>

              {/* (2) 고정 이미지 영역 (글 시작 전 이미지) */}
              {/* 레퍼런스처럼 글 시작 전에 분위기를 잡아주는 이미지를 넣습니다. */}
              <div className="mb-10 overflow-hidden rounded-xl shadow-sm">
                 <div className="relative aspect-[2/1] w-full">
                   {/* [Action] 원하는 기본 이미지가 있다면 아래 src를 수정하세요.
                      현재는 글에 이미지가 있으면 첫 번째 이미지를, 없으면 기본 이미지를 보여주도록 설정 가능합니다.
                      여기서는 '고정된 느낌'을 위해 특정 이미지를 지정하거나, frontmatter의 이미지를 씁니다.
                   */}
                   <Image 
                     src={content.images && content.images[0] ? content.images[0] : '/static/images/twitter-card.png'} 
                     alt={title}
                     fill
                     className="object-cover"
                     priority
                   />
                 </div>
              </div>

              {/* (3) 본문 영역 (Prose) */}
              {/* 폰트 크기와 줄 간격을 레퍼런스(Hobbes)와 비슷하게 조정 */}
              <div className="prose max-w-none text-lg leading-8 text-gray-800 dark:text-gray-300">
                <style jsx global>{`
                  .prose h1, .prose h2, .prose h3 {
                    font-weight: 700;
                    letter-spacing: -0.02em;
                    color: #111;
                    margin-top: 2.5em;
                  }
                  .prose p {
                    margin-top: 1.5em;
                    margin-bottom: 1.5em;
                    line-height: 1.8;
                    color: #374151; /* gray-700 */
                  }
                  .prose a {
                    color: #0ea5e9; /* primary color */
                    text-decoration: none;
                    font-weight: 600;
                  }
                  .prose a:hover {
                    text-decoration: underline;
                  }
                `}</style>
                {children}
              </div>
            </article>

            {/* (4) 하단 네비게이션 (이전 글 / 다음 글) */}
            {(next || prev) && (
              <div className="mt-12 flex justify-between border-t border-gray-200 py-8">
                {prev && (
                  <div className="text-left">
                    <div className="text-xs uppercase tracking-wide text-gray-500">Previous Article</div>
                    <div className="mt-1 text-primary-500 hover:text-primary-600">
                      <Link href={`/blog/${prev.slug}`}>{prev.title}</Link>
                    </div>
                  </div>
                )}
                {next && (
                  <div className="text-right">
                    <div className="text-xs uppercase tracking-wide text-gray-500">Next Article</div>
                    <div className="mt-1 text-primary-500 hover:text-primary-600">
                      <Link href={`/blog/${next.slug}`}>{next.title}</Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* =========================================
              [Right Column] 사이드바 영역 (4칸 차지)
          ========================================= */}
          <aside className="hidden xl:block xl:col-span-4">
            <div className="sticky top-24 pl-8 space-y-10"> {/* 스크롤 시 따라옴 */}
              
              {/* 카테고리별 큐레이션 리스트 */}
              {targetCategories.map((category) => {
                // 해당 카테고리이면서, 현재 보고 있는 글은 제외하고 3개 추출
                const categoryPosts = sortedPosts
                  .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                  .slice(0, 3)

                return (
                  <div key={category} className="group">
                    <div className="flex items-center gap-2 mb-4">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                      <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 group-hover:text-primary-500 transition-colors">
                        {category}
                      </h3>
                    </div>
                    
                    {categoryPosts.length > 0 ? (
                      <ul className="space-y-4">
                        {categoryPosts.map((post) => (
                          <li key={post.slug}>
                            <Link href={`/blog/${post.slug}`} className="group/item block">
                              <h4 className="text-sm font-semibold text-gray-700 transition-colors group-hover/item:text-gray-900 group-hover/item:underline decoration-2 underline-offset-4">
                                {post.title}
                              </h4>
                              {/* 날짜가 필요하다면 주석 해제 */}
                              {/* <span className="text-xs text-gray-400 mt-1 block">{formatDate(post.date, siteMetadata.locale)}</span> */}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-300 italic">업데이트 예정입니다.</p>
                    )}
                  </div>
                )
              })}

            </div>
          </aside>

        </div>
      </SectionContainer>
    </div>
  )
}