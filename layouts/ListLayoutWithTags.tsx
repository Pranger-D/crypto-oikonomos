'use client'

import { usePathname } from 'next/navigation'
import { formatDate } from 'pliny/utils/formatDate'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Blog } from 'contentlayer/generated'
import Link from '@/components/Link'
import Tag from '@/components/Tag'
import siteMetadata from '@/data/siteMetadata'

interface PaginationProps {
  totalPages: number
  currentPage: number
}
interface ListLayoutProps {
  posts: CoreContent<Blog>[]
  title: string
  initialDisplayPosts?: CoreContent<Blog>[]
  pagination?: PaginationProps
}

function Pagination({ totalPages, currentPage }: PaginationProps) {
  const pathname = usePathname()
  const basePath = pathname.replace(/\/page\/\d+$/, '')
  const prevPage = currentPage - 1 > 0
  const nextPage = currentPage + 1 <= totalPages

  return (
    <div className="space-y-2 pb-8 pt-6 md:space-y-5">
      <nav className="flex justify-between text-base font-medium">
        {!prevPage && (
          <button className="cursor-auto opacity-50" disabled={!prevPage}>
            Previous
          </button>
        )}
        {prevPage && (
          <Link href={currentPage - 1 === 1 ? `${basePath}/` : `${basePath}/page/${currentPage - 1}`} rel="prev">
            Previous
          </Link>
        )}
        <span>
          {currentPage} of {totalPages}
        </span>
        {!nextPage && (
          <button className="cursor-auto opacity-50" disabled={!nextPage}>
            Next
          </button>
        )}
        {nextPage && (
          <Link href={`${basePath}/page/${currentPage + 1}`} rel="next">
            Next
          </Link>
        )}
      </nav>
    </div>
  )
}

export default function ListLayoutWithTags({
  posts,
  title,
  initialDisplayPosts = [],
  pagination,
}: ListLayoutProps) {
  const displayPosts = initialDisplayPosts.length > 0 ? initialDisplayPosts : posts

  return (
    <>
      {/* 1. 타이틀 영역 */}
      <div className="pb-8 pt-6 text-center">
        <h1 className="text-3xl font-extrabold leading-9 tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl sm:leading-10 md:text-5xl">
          {title}
        </h1>
      </div>

      {/* 2. 글 목록 영역 (사이드바 제거됨) */}
      <div className="container mx-auto max-w-4xl py-6">
        <ul className="space-y-6">
          {displayPosts.map((post) => {
            const { path, date, title, summary, tags } = post
            return (
              /* [디자인 수정] 흰색 박스 + 그림자 카드 스타일 */
              <li key={path} className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-200 transition-all hover:shadow-md hover:ring-gray-300 dark:bg-gray-800 dark:ring-gray-700 dark:hover:ring-gray-600">
                <article className="flex flex-col space-y-4">
                  
                  {/* 날짜 및 태그 */}
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                    <time dateTime={date}>{formatDate(date, siteMetadata.locale)}</time>
                    <div className="flex gap-2">
                       {tags?.map((tag) => <Tag key={tag} text={tag} />)}
                    </div>
                  </div>

                  {/* 제목 */}
                  <h2 className="text-2xl font-bold leading-8 tracking-tight text-gray-900 dark:text-gray-100">
                    <Link href={`/${path}`} className="group-hover:text-primary-500 transition-colors">
                      {title}
                    </Link>
                  </h2>

                  {/* 요약문 */}
                  <div className="prose max-w-none text-gray-500 dark:text-gray-400 line-clamp-3">
                    {summary}
                  </div>
                  
                  {/* Read More 버튼 (선택 사항) */}
                  <div className="text-right">
                    <Link
                      href={`/${path}`}
                      className="text-sm font-bold uppercase text-primary-500 hover:text-primary-600"
                      aria-label={`Read "${title}"`}
                    >
                      Read more &rarr;
                    </Link>
                  </div>
                </article>
              </li>
            )
          })}
        </ul>
        
        {/* 3. 페이지네이션 */}
        {pagination && pagination.totalPages > 1 && (
          <Pagination currentPage={pagination.currentPage} totalPages={pagination.totalPages} />
        )}
      </div>
    </>
  )
}