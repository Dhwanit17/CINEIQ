export const datasets = [
  {
    id: 'DS_001',
    title: ['MovieLens', '25M'],
    source: 'grouplens.org',
    description:
      '25 million ratings from 162K users on 62K movies. The bedrock of academic recommender research since 1997.',
    stats: [
      { num: '25M', lbl: 'ratings' },
      { num: '62K', lbl: 'titles' },
    ],
  },
  {
    id: 'DS_002',
    title: ['TMDB', 'Metadata'],
    source: 'kaggle / themoviedb',
    description:
      'Cast, crew, genres, keywords, plot summaries, runtime, languages. The descriptive backbone for content-based filtering.',
    stats: [
      { num: '45K', lbl: 'films' },
      { num: '300K', lbl: 'people' },
    ],
  },
  {
    id: 'DS_003',
    title: ['IMDB', '50K Reviews'],
    source: 'kaggle / stanford-ai',
    description:
      'Balanced binary sentiment dataset. Used to fine-tune the DistilBERT classifier feeding the re-ranker.',
    stats: [
      { num: '50K', lbl: 'reviews' },
      { num: '50/50', lbl: 'pos/neg' },
    ],
  },
];
