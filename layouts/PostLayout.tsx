import { ReactNode } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog, Authors } from 'contentlayer/generated'
import Link from '@/components/Link'
import PageTitle from '@/components/PageTitle'
import SectionContainer from '@/components/SectionContainer'
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
    <div className="bg-[#F9FAFB] min-h-screen">
      <ScrollProgressBar />

      {/* [Design Fix 1] 레이아웃 너비를 max-w-7xl로 확장하여 여유 공간 확보 
         기존 max-w-6xl -> max-w-7xl
      */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 xl:px-8">
        <ScrollTopAndComment />
        
        {/* [Design Fix 2] gap-x-24 (96px)로 설정하여 본문과 사이드바를 확실하게 분리 
           기존 gap-x-12 -> gap-x-24
        */}
        <div className="py-12 xl:grid xl:grid-cols-12 xl:gap-x-24">
          
          {/* =========================================
              [Left Column] 메인 콘텐츠 영역 (8.5칸 차지 - 더 넓게)
              기존 col-span-8 -> col-span-9에 가깝게 조정
          ========================================= */}
          <div className="xl:col-span-9">
            <article>
              <header className="mb-10 space-y-6">
                <div className="space-y-3">
                  <div className="text-sm font-medium text-gray-500">
                    <time dateTime={date}>
                      {formatDate(date, siteMetadata.locale)}
                    </time>
                  </div>
                  {/* 제목 크기 조정: 너무 크지 않게 밸런스 조절 */}
                  <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-4xl sm:leading-10 md:text-5xl">
                    {title}
                  </h1>
                </div>
                {/* 구분선 */}
                <div className="h-[1px] w-full bg-gray-300" />
              </header>

              <div className="mb-12 overflow-hidden rounded-xl shadow-sm border border-gray-100">
                 <div className="relative aspect-[2/1] w-full">
                   <Image 
                     src={displayImage}
                     alt={title}
                     fill
                     className="object-cover"
                     priority
                   />
                 </div>
              </div>

              <div className="prose max-w-none text-lg leading-8 text-gray-800 dark:text-gray-300">
                {children}
              </div>
            </article>

            {/* Navigation */}
            {(next || prev) && (
              <div className="mt-16 flex justify-between border-t border-gray-200 py-10">
                {prev && (
                  <div className="text-left max-w-[45%]">
                    <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">Previous Article</div>
                    <div className="text-base text-primary-500 hover:text-primary-600 font-bold leading-snug">
                      <Link href={`/${prev.path}`}>{prev.title}</Link>
                    </div>
                  </div>
                )}
                {next && (
                  <div className="text-right max-w-[45%]">
                    <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">Next Article</div>
                    <div className="text-base text-primary-500 hover:text-primary-600 font-bold leading-snug">
                      <Link href={`/${next.path}`}>{next.title}</Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* =========================================
              [Right Column] 사이드바 영역 (3.5칸 차지)
              "회색 박스 밖" 느낌을 위해 오른쪽 끝으로 밀착
          ========================================= */}
          <aside className="hidden xl:block xl:col-span-3">
            <div className="sticky top-32 space-y-12">
              
              {targetCategories.map((category) => {
                const categoryPosts = sortedPosts
                  .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                  .slice(0, 3)

                return (
                  <div key={category} className="group">
                    {/* [Design Fix 3] 카테고리 타이틀 디자인
                       text-sm (14px) + Bold
                    */}
                    <div className="flex items-center gap-3 mb-5 border-l-2 border-primary-500 pl-3">
                      <h3 className="text-sm font-bold uppercase tracking-widest text-gray-900">
                        {category}
                      </h3>
                    </div>
                    
                    {categoryPosts.length > 0 ? (
                      <ul className="space-y-3 pl-3.5 border-l border-gray-100">
                        {categoryPosts.map((post) => (
                          <li key={post.slug}>
                            <Link href={`/blog/${post.slug}`} className="group/item block py-1">
                              {/* [Design Fix 4] 글 제목 디자인
                                 text-xs (12px) - 카테고리보다 작게 (요청사항 반영)
                                 font-medium - 너무 얇지 않게 가독성 확보
                                 text-gray-500 -> hover: gray-900
                              */}
                              <h4 className="text-xs font-medium text-gray-500 transition-colors group-hover/item:text-gray-900 group-hover/item:underline decoration-1 underline-offset-4 leading-relaxed">
                                {post.title}
                              </h4>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="pl-3 text-xs text-gray-300 italic">No updates.</p>
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