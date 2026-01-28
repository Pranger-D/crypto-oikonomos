import { ReactNode } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import Link from '@/components/Link'
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
    <>
      {/* 1. 진행률 표시줄 & Top 버튼 */}
      <ScrollProgressBar />
      <ScrollTopAndComment />

      {/* [★ 핵심] CSS Breakout Wrapper 
          이 div가 SectionContainer의 감옥을 부수고 화면 전체 너비를 차지합니다.
      */}
      <div className="relative left-[calc(-50vw+50%)] w-screen overflow-x-hidden">
        
        {/* 전체 레이아웃 컨테이너 */}
        <div className="lg:flex w-full min-h-screen">
          
          {/* =========================================
              [Left Column] 메인 콘텐츠 (회색 배경)
              - PC: 화면의 75% 차지, 회색 배경
              - Mobile: 전체 차지, 흰색 배경
          ========================================= */}
          <main className="w-full lg:w-[75%] bg-white lg:bg-[#F9FAFB]">
            {/* 콘텐츠 내부 정렬: 
                화면이 너무 넓어지면 글이 왼쪽 구석에 박히지 않도록,
                오른쪽 여백(mr)을 주어 사이드바와 자연스럽게 멀어지게 배치 
            */}
            <div className="mx-auto max-w-3xl px-6 py-10 lg:ml-auto lg:mr-16 xl:mr-24 xl:max-w-4xl lg:py-20">
              
              <article>
                <header className="mb-10 lg:mb-14 space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm font-bold text-gray-500">
                      <time dateTime={date}>{formatDate(date, siteMetadata.locale)}</time>
                      {tags && <span className="lg:hidden text-primary-500">#{tags[0]}</span>}
                    </div>
                    <h1 className="text-3xl font-extrabold leading-tight text-gray-900 sm:text-4xl md:text-5xl lg:text-[3.25rem]">
                      {title}
                    </h1>
                  </div>
                  <div className="h-[1px] w-full bg-gray-200 lg:bg-gray-300" />
                </header>

                {/* 이미지 */}
                <div className="mb-10 lg:mb-16 overflow-hidden rounded-xl bg-gray-100 shadow-sm">
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

                {/* 본문 */}
                <div className="prose prose-lg max-w-none text-gray-800 dark:text-gray-300 leading-8 break-keep">
                  {children}
                </div>
              </article>

              {/* 네비게이션 */}
              {(next || prev) && (
                <div className="mt-20 flex flex-col gap-8 border-t border-gray-200 lg:border-gray-300 pt-10 sm:flex-row sm:justify-between">
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
              [Right Column] 사이드바 (흰색 배경)
              - PC: 화면의 25% 차지, 흰색 배경, 경계선 있음
              - Mobile: 숨김
          ========================================= */}
          <aside className="hidden lg:block lg:w-[25%] bg-white border-l border-gray-100">
            <div className="sticky top-0 h-screen overflow-y-auto px-8 py-20 xl:px-12">
              <div className="space-y-12">
                {targetCategories.map((category) => {
                  const categoryPosts = sortedPosts
                    .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                    .slice(0, 3)

                  return (
                    <div key={category} className="group">
                      <div className="flex items-center gap-3 mb-5">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                        <h3 className="text-sm font-black uppercase tracking-widest text-gray-900">
                          {category}
                        </h3>
                      </div>
                      
                      {categoryPosts.length > 0 ? (
                        <ul className="space-y-4">
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
            </div>
          </aside>

        </div>
      </div>
    </>
  )
}