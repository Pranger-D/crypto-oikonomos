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
  
  const displayImage = content.images && content.images[0] ? content.images[0] : '/static/images/twitter-card.png'

  return (
    // 전체 페이지 컨테이너
    <div className="min-h-screen bg-white">
      <ScrollProgressBar />
      <ScrollTopAndComment />

      {/* [Layout Strategy] 
         PC: 좌측(회색) / 우측(흰색)으로 화면 분할 (Grid)
         Mobile: 전체 흰색, 블록 쌓기 (Block)
      */}
      <div className="lg:flex w-full">
        
        {/* =========================================
            [Left Column] 메인 콘텐츠 영역 (회색 배경)
            - PC: w-[75%] (화면의 3/4), 회색 배경
            - Mobile: w-full, 흰색 배경
        ========================================= */}
        <main className="w-full lg:w-[75%] bg-white lg:bg-[#F3F4F6] min-h-screen">
          {/* 콘텐츠 내부 여백 컨테이너 */}
          {/* 모바일: px-4 (여백 최소화), PC: px-16 ~ px-32 (중앙 정렬 느낌) */}
          <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-12 lg:py-20 xl:px-24">
            
            <article>
              <header className="mb-8 lg:mb-12 space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-sm font-bold text-gray-500">
                    <time dateTime={date}>
                      {formatDate(date, siteMetadata.locale)}
                    </time>
                    {tags && (
                       <span className="lg:hidden text-primary-500">#{tags[0]}</span>
                    )}
                  </div>
                  {/* 제목 크기 및 자간 조절 */}
                  <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-4xl md:text-5xl lg:text-[3.5rem]">
                    {title}
                  </h1>
                </div>
                {/* 구분선 (PC에서는 진하게, 모바일은 연하게) */}
                <div className="h-[1px] w-full bg-gray-200 lg:bg-gray-300" />
              </header>

              {/* 고정 이미지 */}
              <div className="mb-10 lg:mb-16 overflow-hidden rounded-lg lg:rounded-2xl bg-gray-200 shadow-sm">
                 <div className="relative aspect-[16/9] w-full">
                   <Image 
                     src={displayImage}
                     alt={title}
                     fill
                     className="object-cover"
                     priority
                   />
                 </div>
              </div>

              {/* 본문 (Typography) */}
              {/* 모바일 가독성을 위해 break-words 추가 */}
              <div className="prose prose-lg max-w-none break-keep text-gray-800 dark:text-gray-300 leading-8 lg:leading-9">
                {children}
              </div>
            </article>

            {/* 하단 네비게이션 */}
            {(next || prev) && (
              <div className="mt-16 flex flex-col gap-8 border-t border-gray-200 lg:border-gray-300 pt-10 sm:flex-row sm:justify-between">
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
          </div>
        </main>

        {/* =========================================
            [Right Column] 사이드바 영역 (흰색 배경)
            - PC: w-[25%] (화면의 1/4), 흰색 배경, 왼쪽 경계선
            - Mobile: Hidden (숨김)
        ========================================= */}
        <aside className="hidden lg:block lg:w-[25%] bg-white border-l border-gray-100">
          <div className="sticky top-0 h-screen overflow-y-auto px-8 py-20">
            
            <div className="space-y-16">
              {targetCategories.map((category) => {
                const categoryPosts = sortedPosts
                  .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                  .slice(0, 3)

                return (
                  <div key={category} className="group">
                    {/* 카테고리 타이틀 */}
                    <div className="flex items-center gap-3 mb-6">
                      <div className="h-2 w-2 rounded-full bg-primary-500" />
                      <h3 className="text-sm font-black uppercase tracking-widest text-gray-900">
                        {category}
                      </h3>
                    </div>
                    
                    {categoryPosts.length > 0 ? (
                      <ul className="space-y-5">
                        {categoryPosts.map((post) => (
                          <li key={post.slug}>
                            <Link href={`/blog/${post.slug}`} className="group/item block">
                              <h4 className="text-xs font-medium text-gray-500 transition-colors group-hover/item:text-primary-600 leading-relaxed hover:underline decoration-1 underline-offset-4">
                                {post.title}
                              </h4>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-300 italic">No updates.</p>
                    )}
                  </div>
                )
              })}
            </div>

            {/* 여백 채우기용 장식 (선택사항) */}
            <div className="mt-20 pt-10 border-t border-gray-50 text-xs text-gray-300">
              © 2026 Crypto Oikonomos
            </div>
          </div>
        </aside>

      </div>
    </div>
  )
}