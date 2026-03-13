export const WUWA_CHARACTERS = [
  { id: 'fulolo', name: '弗洛洛', element: '光', rarity: 5 },
  { id: 'luhesi', name: '陆赫斯', element: '暗', rarity: 5 },
  { id: 'aimisi', name: '爱弥斯', element: '光', rarity: 5 },
  { id: 'jina', name: '吉纳', element: '火', rarity: 4 },
  { id: 'weina', name: '维娜', element: '水', rarity: 4 },
  { id: 'mofei', name: '莫菲', element: '风', rarity: 4 },
  { id: 'kailin', name: '凯琳', element: '土', rarity: 4 },
  { id: 'ailin', name: '艾琳', element: '光', rarity: 4 },
  { id: 'xiweier', name: '希维尔', element: '暗', rarity: 5 },
  { id: 'leina', name: '蕾娜', element: '火', rarity: 5 },
  { id: 'nami', name: '娜米', element: '水', rarity: 5 },
  { id: 'feier', name: '菲尔', element: '风', rarity: 5 },
  { id: 'diana', name: '黛安娜', element: '土', rarity: 5 },
  { id: 'liya', name: '莉雅', element: '光', rarity: 4 },
  { id: 'saiya', name: '赛亚', element: '暗', rarity: 4 },
  { id: 'qiao', name: '乔', element: '火', rarity: 4 },
  { id: 'lina', name: '莉娜', element: '水', rarity: 4 },
  { id: 'feng', name: '风', element: '风', rarity: 4 },
  { id: 'tu', name: '图', element: '土', rarity: 4 },
] as const

export type CharacterId = typeof WUWA_CHARACTERS[number]['id']
