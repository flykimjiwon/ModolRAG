import { createContext, useContext, useState, type ReactNode } from 'react'

type Locale = 'ko' | 'en'

const T = {
  'nav.documents': { ko: '문서 관리', en: 'Documents' },
  'nav.collections': { ko: '컬렉션', en: 'Collections' },
  'nav.search': { ko: '검색', en: 'Search' },
  'nav.graph': { ko: '지식 그래프', en: 'Graph' },
  'nav.settings': { ko: '설정', en: 'Settings' },
  'nav.api': { ko: 'API 문서', en: 'API Docs' },
  'docs.title': { ko: '문서 관리', en: 'Documents' },
  'docs.upload': { ko: '파일 업로드', en: 'Upload File' },
  'docs.uploading': { ko: '업로드 중...', en: 'Uploading...' },
  'docs.empty': { ko: '문서가 없습니다. 파일을 업로드하세요.', en: 'No documents yet. Upload one to get started.' },
  'docs.name': { ko: '이름', en: 'Name' },
  'docs.type': { ko: '유형', en: 'Type' },
  'docs.status': { ko: '상태', en: 'Status' },
  'docs.chunks': { ko: '청크', en: 'Chunks' },
  'docs.date': { ko: '날짜', en: 'Date' },
  'docs.delete': { ko: '삭제', en: 'Delete' },
  'docs.confirm': { ko: '이 문서를 삭제하시겠습니까?', en: 'Delete this document?' },
  'coll.title': { ko: '컬렉션', en: 'Collections' },
  'coll.name': { ko: '컬렉션 이름', en: 'Collection name' },
  'coll.desc': { ko: '설명', en: 'Description' },
  'coll.create': { ko: '생성', en: 'Create' },
  'coll.in': { ko: '포함된 문서', en: 'Documents in collection' },
  'coll.available': { ko: '추가 가능한 문서', en: 'Available documents' },
  'coll.no_docs': { ko: '할당된 문서가 없습니다.', en: 'No documents assigned.' },
  'coll.all_in': { ko: '모든 문서가 포함되어 있습니다.', en: 'All documents are in this collection.' },
  'coll.select': { ko: '컬렉션을 선택하세요', en: 'Select a collection' },
  'coll.empty': { ko: '컬렉션이 없습니다', en: 'No collections yet' },
  'coll.add': { ko: '추가', en: 'Add' },
  'coll.remove': { ko: '제거', en: 'Remove' },
  'coll.confirm': { ko: '이 컬렉션을 삭제하시겠습니까?', en: 'Delete this collection?' },
  'coll.docs': { ko: '개 문서', en: ' docs' },
  'search.title': { ko: '검색', en: 'Search' },
  'search.placeholder': { ko: '검색어를 입력하세요...', en: 'Enter search query...' },
  'search.button': { ko: '검색', en: 'Search' },
  'search.searching': { ko: '검색 중...', en: 'Searching...' },
  'search.all': { ko: '전체 문서', en: 'All Documents' },
  'search.results': { ko: '개 결과 · ', en: ' results in ' },
  'search.no_results': { ko: '결과가 없습니다.', en: 'No results found.' },
  'graph.title': { ko: '지식 그래프', en: 'Knowledge Graph' },
  'graph.empty': { ko: '그래프 데이터가 없습니다.', en: 'No graph data yet.' },
  'graph.loading': { ko: '로딩 중...', en: 'Loading...' },
  'graph.close': { ko: '닫기', en: 'Close' },
  'settings.title': { ko: '설정', en: 'Settings' },
  'settings.api_key': { ko: 'API 키', en: 'API Key' },
  'settings.api_hint': { ko: '브라우저에 저장됩니다', en: 'Stored in browser' },
  'settings.chunk_size': { ko: '청크 크기', en: 'Chunk Size' },
  'settings.chunk_overlap': { ko: '청크 오버랩', en: 'Chunk Overlap' },
  'settings.model': { ko: '임베딩 모델', en: 'Embedding Model' },
  'settings.top_k': { ko: '검색 결과 수', en: 'Top-K' },
  'settings.threshold': { ko: '유사도 임계값', en: 'Threshold' },
  'settings.save': { ko: '저장', en: 'Save' },
  'settings.saved': { ko: '저장됨!', en: 'Saved!' },
} as const

type TKey = keyof typeof T
interface Ctx { locale: Locale; setLocale: (l: Locale) => void; t: (k: TKey) => string }
const I18nCtx = createContext<Ctx>({ locale: 'ko', setLocale: () => {}, t: (k) => k })

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem('modolrag-locale') as Locale) || 'ko')
  const change = (l: Locale) => { setLocale(l); localStorage.setItem('modolrag-locale', l) }
  const t = (k: TKey) => T[k]?.[locale] || k
  return <I18nCtx.Provider value={{ locale, setLocale: change, t }}>{children}</I18nCtx.Provider>
}

export const useI18n = () => useContext(I18nCtx)
