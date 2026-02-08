'use client'

import Link from '@/components/Link'

interface BlogPost {
    slug: string
    title: string
    category: string
}

interface BlogPostsListProps {
    selectedDate: string | null
    posts: BlogPost[]
}

export default function BlogPostsList({ selectedDate, posts }: BlogPostsListProps) {
    if (!selectedDate) {
        return (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                    📝 관련 블로그 글
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
                    차트에서 날짜를 클릭하면 해당일의 블로그 글을 확인할 수 있습니다.
                </p>
            </div>
        )
    }

    if (posts.length === 0) {
        return (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                    📝 관련 블로그 글
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                    선택한 날짜: <span className="font-semibold">{selectedDate}</span>
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
                    이 날짜에 작성된 글이 없습니다.
                </p>
            </div>
        )
    }

    return (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">📝 관련 블로그 글</h3>
                <span className="text-sm text-gray-500 dark:text-gray-400">{selectedDate}</span>
            </div>

            <div className="space-y-3">
                {posts.map((post, index) => (
                    <Link
                        key={index}
                        href={`/blog/${post.slug}`}
                        className="block group p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-md transition-all"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <p className="text-sm font-bold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                    {post.title}
                                </p>
                            </div>
                            <span className="ml-3 text-xs font-semibold px-2 py-1 rounded bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200">
                                {post.category}
                            </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            클릭하여 전체 글 읽기 →
                        </p>
                    </Link>
                ))}
            </div>
        </div>
    )
}
