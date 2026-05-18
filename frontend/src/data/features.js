export const features = [
  {
    icon: '🧠',
    num: '01 / 04',
    title: ['Hybrid', 'Recommendation', 'Engine'],
    body: 'Three signals, fused into one ranking: user-item collaborative filtering, TF-IDF cosine similarity over plot embeddings, and SVD matrix factorization for latent taste.',
    tags: ['CF', 'TF-IDF', 'SVD', 'cosine'],
  },
  {
    icon: '🎭',
    num: '02 / 04',
    title: ['Sentiment-Aware', 'Re-Ranker'],
    body: 'The output of the hybrid engine is re-scored by sentiment signals extracted from real user reviews — VADER for speed at scale, DistilBERT when nuance matters.',
    tags: ['VADER', 'DistilBERT', 're-rank'],
  },
  {
    icon: '📊',
    num: '03 / 04',
    title: ['User Taste', 'Dashboard'],
    // bodyJsx supports inline emphasis. Rendered manually in Features.jsx.
    bodyParts: [
      'Genre radar charts. Decade heatmaps. Director and actor affinity scores. See not just what you watch, but the ',
      { em: 'shape' },
      ' of your taste — and where it might grow.',
    ],
    tags: ['Plotly', 'Streamlit', 'radar'],
  },
  {
    icon: '💡',
    num: '04 / 04',
    title: ['Explainability', 'Layer'],
    body: 'Every recommendation comes with a human-readable reason. LIME for feature attribution on the ML side, rule-based templates for narrative clarity. No black boxes.',
    tags: ['LIME', 'templates', 'transparent'],
  },
];
