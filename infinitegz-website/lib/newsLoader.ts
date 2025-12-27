import newsData from '@/data/news.json'

export type Language = 'en' | 'zh' | 'ms'

export interface NewsItem {
  id: string
  date: string
  title: {
    en: string
    zh: string
    ms: string
  }
  category: {
    en: string
    zh: string
    ms: string
  }
  description: {
    en: string
    zh: string
    ms: string
  }
}

export interface LocalizedNewsItem {
  id: string
  date: string
  title: string
  category: string
  description: string
}

/**
 * Get news items for a specific language
 */
export function getNews(language: Language): LocalizedNewsItem[] {
  return newsData.items.map((item: any) => ({
    id: item.id,
    date: item.date,
    title: item.title[language],
    category: item.category[language],
    description: item.description[language],
  }))
}

/**
 * Get all news items (with all language versions)
 */
export function getAllNews(): NewsItem[] {
  return newsData.items as NewsItem[]
}

/**
 * Get a single news item by ID
 */
export function getNewsById(id: string, language: Language): LocalizedNewsItem | null {
  const item = newsData.items.find((item: any) => item.id === id)
  if (!item) return null
  
  return {
    id: item.id,
    date: item.date,
    title: item.title[language],
    category: item.category[language],
    description: item.description[language],
  }
}
