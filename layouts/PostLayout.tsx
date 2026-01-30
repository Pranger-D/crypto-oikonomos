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
  const displayImage = content.images && content.images[0] ? content.images[0] : '/static/images/common-hero.webp'

  return (
    <>
      <ScrollProgressBar />
      <ScrollTopAndComment />

      {/* [수정 1] overflow-x-hidden 제거 
          - sticky가 작동하지 않게 만드는 원인을 제거했습니다.
          - w-screen을 유지하여 화면 전체 너비를 씁니다.
      */}
      <div className="w-full overflow-x-hidden lg:relative lg:left-[calc(-50vw+50%)] lg:w-screen lg:overflow-x-visible">
        
        {/* [수정 2] Flex 정렬 및 간격 조정
            - justify-center: 박스들을 화면 가운데로 모읍니다.
            - gap-5: 회색 박스와 네비게이션 사이를 넉넉하게(20px) 띄웁니다.
        */}
        <div className="lg:flex lg:justify-center lg:gap-3 w-full min-h-screen">
          
          {/* =========================================
              [Left Column] 메인 콘텐츠 (회색 배경)
              - lg:w-[950px]: 회색 박스 너비 (숫자를 조절하여 크기 변경 가능)
              - lg:px-6 : 회색 박스 여백 24px
          ========================================= */}
          <main className="w-full lg:w-[900px] bg-white lg:bg-[#FCFCFF] lg:rounded-3xl lg:my-10 h-fit">
            <div className="mx-auto max-w-full px-2 py-10 lg:px-10 lg:py-16">
              
              <article>
                <header className="mb-10 lg:mb-14 space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm font-bold text-gray-500">
                      <time dateTime={date}>{formatDate(date, siteMetadata.locale)}</time>
                      {tags && <span className="lg:hidden text-primary-500">#{tags[0]}</span>}
                    </div>
                    
                    {/* [타이포그래피 전략]
                        - text-xl (20px): 모바일 (작고 깔끔하게)
                         - md:text-2xl (24px): 태블릿 (중간 크기 추가)
                         - lg:text-2xl (24px): PC (시원하게, 하지만 부담스럽지 않게)
                    */}
                    <h1 className="text-xl font-bold leading-tight text-gray-900 md:text-2xl lg:text-2xl">
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
                       priority // LCP 성능 향상을 위해 필수
                       sizes="(max-width: 768px) 100vw, (max-width: 1200px) 800px" 
                     />
                   </div>
                </div>

                {/* 본문 */}
                <div className="prose lg:prose-lg max-w-none text-gray-800 dark:text-gray-300 leading-8 break-keep">
                  {children}
                </div>
              </article>

              {/* 하단 네비게이션 */}
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
              [Right Column] 사이드바 영역 (레일)
              - sticky가 작동하려면 부모(aside)가 충분히 길어야 합니다.
              - lg:w-[200px]: 공간을 미리 확보해둡니다.
          ========================================= */}
          <aside className="hidden lg:block lg:w-[200px] lg:my-10">
            
            {/* [Navigation Box] 움직이는 박스 (기차) 
                - sticky top-10: 화면 상단에서 40px 떨어진 곳에 고정
                - w-[200px]: 네비게이션 너비
                - h-fit: 내용물만큼만 크기 차지
            */}
            <div className="sticky top-10 w-[200px] h-fit bg-white border border-gray-200 shadow-sm rounded-xl p-5">
              <div className="space-y-8">
                {targetCategories.map((category) => {
                  const categoryPosts = sortedPosts
                    .filter(p => p.tags.some(t => t.toUpperCase() === category.toUpperCase()) && p.slug !== slug)
                    .slice(0, 3)

                  return (
                    <div key={category} className="group">
                      <div className="flex items-center gap-2 mb-3 border-b border-gray-100 pb-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                        <h3 className="text-xs font-bold uppercase tracking-widest text-gray-900">
                          {category}
                        </h3>
                      </div>
                      
                      {categoryPosts.length > 0 ? (
                        <ul className="space-y-3">
                          {categoryPosts.map((post) => (
                            <li key={post.slug}>
                              <Link href={`/blog/${post.slug}`} className="group/item block">
                                <h4 className="text-xs font-medium text-gray-500 transition-colors group-hover/item:text-gray-900 group-hover/item:underline decoration-1 underline-offset-4 leading-relaxed">
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