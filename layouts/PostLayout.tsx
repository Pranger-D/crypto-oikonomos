import { ReactNode } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import Link from '@/components/Link'
import PageTitle from '@/components/PageTitle'
import Image from '@/components/Image'
import siteMetadata from '@/data/siteMetadata'
import ScrollTopAndComment from '@/components/ScrollTopAndComment'
import ScrollProgressBar from '@/components/ScrollProgressBar'
import { formatDate } from 'pliny/utils/formatDate'

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

  const sortedPosts = sortPosts(allBlogs)
  const targetCategories = ['Briefing', 'Insight', 'Study']
  
  // 이미지: 없으면 기본 이미지
  const displayImage = content.images && content.images[0] ? content.images[0] : '/static/images/twitter-card.png'

  return (
    // [Layout Fix 1] 배경색 전략 변경
    // 모바일(기본): 흰색(bg-white) -> 글자가 꽉 차게 보임
    // PC(lg 이상): 회색(bg-gray-50) -> 카드시스템 적용
    <div className="bg-white lg:bg-gray-50 min-h-screen">
      
      {/* 진행률 표시줄 */}
      <ScrollProgressBar />

      {/* [Layout Fix 2] SectionContainer 제거하고 직접 너비 통제 */}
      {/* max-w-[1440px]로 더 넓게 잡아서 사이드바 공간 확보 */}
      <div className="mx-auto max-w-[1440px] px-0 lg:px-6 xl:px-12">
        <ScrollTopAndComment />
        
        {/* 그리드 시스템 */}
        <div className="lg:grid lg:grid-cols-12 lg:gap-12 lg:py-12">
          
          {/* =========================================
              [Left Column] 메인 콘텐츠 (하얀색 카드)
              - 모바일: 카드 느낌 없음, 전체 너비 사용
              - PC: 하얀색 박스(shadow) 안에 글이 들어감
          ========================================= */}
          <main className="lg:col-span-8 xl:col-span-9 bg-white lg:rounded-3xl lg:shadow-sm lg:border lg:border-gray-100 lg:p-12 p-5 pt-10">
            <article>
              <header className="mb-8 lg:mb-10 space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-sm font-medium text-gray-500">
                    <time dateTime={date}>
                      {formatDate(date, siteMetadata.locale)}
                    </time>
                    {/* 모바일에서만 보이는 태그 (PC는 사이드바에 있으므로) */}
                    {tags && (
                       <span className="lg:hidden text-primary-500 font-bold">#{tags[0]}</span>
                    )}
                  </div>
                  <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-4xl md:text-5xl">
                    {title}
                  </h1>
                </div>
                {/* 구분선 */}
                <div className="h-[1px] w-full bg-gray-200" />
              </header>

              {/* 고정 이미지 */}
              <div className="mb-10 lg:mb-12 overflow-hidden rounded-xl bg-gray-100">
                 <div className="relative aspect-[16/9] w-full">
                   <Image 
                     src={displayImage}
                     alt={title}
                     fill
                     className="object-cover transition-transform duration-500 hover:scale-105"
                     priority
                   />
                 </div>
              </div>

              {/* 본문 */}
              {/* prose-lg로 글자 크기 키움 + 모바일 좌우 여백 확보 */}
              <div className="prose prose-lg max-w-none text-gray-800 dark:text-gray-300 leading-8">
                {children}
              </div>
            </article>

            {/* 하단 네비게이션 (이전/다음 글) */}
            {(next || prev) && (
              <div className="mt-16 flex flex-col gap-6 border-t border-gray-100 pt-10 sm:flex-row sm:justify-between">
                {prev && (
                  <div className="flex flex-col items-start text-left sm:w-1/2">
                    <span className="text-xs uppercase tracking-wider text-gray-400 font-bold mb-2">Previous</span>
                    <Link href={`/${prev.path}`} className="text-lg font-bold text-gray-900 hover:text-primary-500 leading-snug">
                      {prev.title}
                    </Link>
                  </div>
                )}
                {next && (
                  <div className="flex flex-col items-end text-right sm:w-1/2">
                    <span className="text-xs uppercase tracking-wider text-gray-400 font-bold mb-2">Next</span>
                    <Link href={`/${next.path}`} className="text-lg font-bold text-gray-900 hover:text-primary-500 leading-snug">
                      {next.title}
                    </Link>
                  </div>
                )}
              </div>
            )}
          </main>

          {/* =========================================
              [Right Column] 사이드바 (투명 배경)
              - 모바일: 숨김 (Hidden) -> 글 읽기에 집중
              - PC: 하얀색 박스 밖(회색 배경 위)에 둥둥 떠있음
          ========================================= */}
          <aside className="hidden lg:block lg:col-span-4 xl:col-span-3">
            <div className="sticky top-24 space-y-12 pl-4">
              
              {targetCategories.map((category) => {
                const categoryPosts = sortedPosts
                  .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                  .slice(0, 3)

                return (
                  <div key={category} className="group">
                    {/* 카테고리 타이틀 (회색 배경 위에 바로 글씨) */}
                    <div className="flex items-center justify-between mb-5 border-b border-gray-200 pb-2">
                      <h3 className="text-sm font-black uppercase tracking-widest text-gray-400 group-hover:text-gray-900 transition-colors">
                        {category}
                      </h3>
                      <span className="text-[10px] bg-white px-2 py-0.5 rounded-full text-gray-400 border border-gray-100 shadow-sm">
                        {categoryPosts.length} posts
                      </span>
                    </div>
                    
                    {categoryPosts.length > 0 ? (
                      <ul className="space-y-4">
                        {categoryPosts.map((post) => (
                          <li key={post.slug}>
                            <Link href={`/blog/${post.slug}`} className="group/item block">
                              {/* 글 제목: 카테고리보다 작게, 하지만 명확하게 */}
                              <h4 className="text-[13px] font-medium text-gray-600 transition-colors group-hover/item:text-primary-600 leading-relaxed hover:underline decoration-1 underline-offset-4">
                                {post.title}
                              </h4>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No updates.</p>
                    )}
                  </div>
                )
              })}

            </div>
          </aside>

        </div>
      </div>
    </div>
  )
}