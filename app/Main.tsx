import Link from '@/components/Link'
import Tag from '@/components/Tag'
import siteMetadata from '@/data/siteMetadata'
import { formatDate } from 'pliny/utils/formatDate'
import NewsletterForm from 'pliny/ui/NewsletterForm'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'

// 3단 카테고리 정의 (여기에 정의된 태그가 글에 있어야 화면에 나옵니다)
const TARGET_CATEGORIES = ['Briefing', 'Insight', 'Study']

export default function Home({ posts }: { posts: CoreContent<Blog>[] }) {
  // 1. 최신 글 3개 (카드 섹션용)
  const latestPosts = posts.slice(0, 3)

  return (
    <>
      {/* ==========================================
          Section 1: Hero Image (The White Horizon) 
          - 압도적인 설원 이미지와 하단 화이트 페이딩
      ========================================== */}
      <div className="relative -mx-4 mb-16 sm:-mx-6 md:-mx-12 lg:-mx-20">
        <div className="relative h-[450px] w-full overflow-hidden md:h-[600px]">
          {/* 배경 이미지 (설원/구름 등 밝은 톤 권장) */}
          <div 
            className="absolute inset-0 bg-cover bg-center"
            style={{ 
              backgroundImage: "url('/static/images/main.avif')",
            }} 
          />
          
          {/* 그라데이션: 이미지가 아래로 갈수록 흰색 배경과 자연스럽게 섞임 */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-white" />

          {/* 히어로 텍스트 */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
            <h1 className="text-4xl font-extrabold text-white drop-shadow-lg sm:text-5xl md:text-7xl">
              {siteMetadata.headerTitle}
            </h1>
            <p className="mt-4 text-lg font-medium text-gray-100 drop-shadow-md sm:text-xl max-w-2xl">
              {siteMetadata.description}
            </p>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        
        {/* ==========================================
            Section 2: Latest Updates (최신 글 3개)
        ========================================== */}
        <div className="space-y-4 pb-12">
          <div className="flex items-end justify-between border-b border-gray-100 pb-4">
            <div>
              <h2 className="text-3xl font-bold leading-9 tracking-tight text-gray-900 dark:text-gray-100">
                Latest Updates
              </h2>
              <p className="mt-1 text-gray-500 dark:text-gray-400">최신 시장 분석과 인사이트</p>
            </div>
            <Link href="/blog" className="text-sm font-semibold text-primary-500 hover:text-primary-600">
              View All &rarr;
            </Link>
          </div>
          
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3 pt-6">
            {!posts.length && <p className="text-gray-500">포스팅이 없습니다.</p>}
            {latestPosts.map((post) => {
              const { slug, date, title, summary, tags } = post
              return (
                <div key={slug} className="group flex flex-col justify-between rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:bg-gray-800 dark:border-gray-700">
                  <div>
                    <div className="mb-3 flex items-center justify-between">
                      <time className="text-xs font-semibold text-gray-400" dateTime={date}>
                        {formatDate(date, siteMetadata.locale)}
                      </time>
                      {tags[0] && <span className="text-xs font-bold text-primary-500">#{tags[0]}</span>}
                    </div>
                    <h3 className="mb-3 text-xl font-bold leading-snug text-gray-900 group-hover:text-primary-600 dark:text-gray-100 dark:group-hover:text-primary-400">
                      <Link href={`/blog/${slug}`}>
                        {title}
                      </Link>
                    </h3>
                    <p className="mb-4 text-sm text-gray-500 line-clamp-3 leading-relaxed dark:text-gray-400">
                      {summary}
                    </p>
                  </div>
                  <div className="mt-auto pt-4 border-t border-gray-100 dark:border-gray-700">
                    <Link href={`/blog/${slug}`} className="text-sm font-semibold text-primary-500 hover:text-primary-600">
                      Read more &rarr;
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ==========================================
            Section 3: Curated Collections (3단 분류)
            Briefing / Insight / Study
        ========================================== */}
        <div className="space-y-4 pt-12 pb-12">
          <h2 className="text-3xl font-bold leading-9 tracking-tight text-gray-900 dark:text-gray-100">
            Curated Collections
          </h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3 pt-4">
            {TARGET_CATEGORIES.map((category) => {
              // 해당 카테고리(태그)를 가진 글만 필터링 (최신순 5개)
              const categoryPosts = posts.filter(p => 
                p.tags.some(t => t.toUpperCase() === category.toUpperCase())
              ).slice(0, 5)
              
              return (
                <div key={category} className="rounded-2xl bg-gray-50 p-6 dark:bg-gray-800/50">
                  <div className="mb-6 flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-primary-500" />
                    <h3 className="text-xl font-extrabold uppercase tracking-widest text-gray-800 dark:text-gray-200">
                      {category}
                    </h3>
                  </div>
                  
                  {categoryPosts.length > 0 ? (
                    <ul className="space-y-4">
                      {categoryPosts.map((post) => (
                        <li key={post.slug} className="group flex flex-col border-b border-gray-200 pb-3 last:border-0 dark:border-gray-700">
                          <Link href={`/blog/${post.slug}`} className="font-semibold text-gray-700 transition-colors group-hover:text-primary-600 dark:text-gray-300 dark:group-hover:text-primary-400">
                            {post.title}
                          </Link>
                          <span className="mt-1 text-xs text-gray-400">
                            {formatDate(post.date, siteMetadata.locale)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="flex h-32 flex-col items-center justify-center text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-xl dark:border-gray-700">
                      <p>아직 등록된 글이 없습니다.</p>
                      <p className="text-xs mt-1 text-primary-400">#{category} 태그를 추가하세요</p>
                    </div>
                  )}
                  
                  <div className="mt-6">
                    <Link href={`/tags/${category.toLowerCase()}`} className="text-xs font-bold uppercase text-gray-400 hover:text-primary-500">
                      View all {category} &rarr;
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 뉴스레터 폼 (하단에 살려둠, 필요 없으면 삭제 가능) */}
      {siteMetadata.newsletter?.provider && (
        <div className="flex items-center justify-center pt-8">
          <NewsletterForm />
        </div>
      )}
    </>
  )
}