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
  const sortedPosts = sortPosts(allBlogs)
  const targetCategories = ['Briefing', 'Insight', 'Study']
  
  // 이미지 처리 (없으면 기본 이미지)
  const displayImage = content.images && content.images[0] ? content.images[0] : '/static/images/twitter-card.png'

  return (
    <div className="bg-[#F9FAFB] min-h-screen">
      
      {/* 1. 상단 진행률 표시줄 */}
      <ScrollProgressBar />

      <SectionContainer>
        <ScrollTopAndComment />
        
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 xl:grid xl:grid-cols-12 xl:gap-x-12 xl:px-0">
          
          {/* [Left Column] 메인 콘텐츠 영역 (8칸) */}
          <div className="xl:col-span-8">
            <article>
              {/* (1) 헤더 영역 */}
              <header className="mb-8 space-y-4">
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-500">
                    <time dateTime={date}>
                      {formatDate(date, siteMetadata.locale)}
                    </time>
                  </div>
                  <PageTitle>{title}</PageTitle>
                </div>
                {/* 구분선 */}
                <div className="h-[1px] w-full bg-gray-300" />
              </header>

              {/* (2) 고정 이미지 영역 */}
              <div className="mb-10 overflow-hidden rounded-xl shadow-sm border border-gray-100">
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

              {/* (3) 본문 영역 (스타일은 tail.css로 이사감) */}
              <div className="prose max-w-none text-lg leading-8 text-gray-800 dark:text-gray-300">
                {children}
              </div>
            </article>

            {/* (4) 하단 네비게이션 */}
            {(next || prev) && (
              <div className="mt-12 flex justify-between border-t border-gray-200 py-8">
                {prev && (
                  <div className="text-left">
                    <div className="text-xs uppercase tracking-wide text-gray-500">Previous Article</div>
                    <div className="mt-1 text-primary-500 hover:text-primary-600 font-medium">
                      <Link href={`/${prev.path}`}>{prev.title}</Link>
                    </div>
                  </div>
                )}
                {next && (
                  <div className="text-right">
                    <div className="text-xs uppercase tracking-wide text-gray-500">Next Article</div>
                    <div className="mt-1 text-primary-500 hover:text-primary-600 font-medium">
                      <Link href={`/${next.path}`}>{next.title}</Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* [Right Column] 사이드바 영역 (4칸) */}
          <aside className="hidden xl:block xl:col-span-4">
            <div className="sticky top-24 pl-8 space-y-10">
              
              {/* 카테고리별 큐레이션 리스트 */}
              {targetCategories.map((category) => {
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