// Demo recommendation data. Reasons contain inline HTML
// (a <span class="hl"> wrapping highlighted phrases) preserved
// from the original markup. Rendered via dangerouslySetInnerHTML
// in Demo.jsx, which is safe here because the strings are static
// and authored by us — never user input.

export const demoData = {
  'Blade Runner 2049': {
    meta: { genre: 'sci-fi · neo-noir', mood: 'contemplative', runtime: '2h 44m' },
    recs: [
      { title: 'Solaris', year: 1972, score: 94, reason: "Both films use slow pacing and existential melancholy to explore <span class='hl'>identity and memory</span> through a sci-fi lens.", cf: 88, sent: 92 },
      { title: 'Ex Machina', year: 2014, score: 91, reason: "Shared themes of <span class='hl'>artificial consciousness</span> and the moral weight of creating sentient beings.", cf: 85, sent: 89 },
      { title: 'Arrival', year: 2016, score: 89, reason: "Denis Villeneuve's signature <span class='hl'>contemplative sci-fi</span> aesthetic and patient narrative structure.", cf: 91, sent: 87 },
      { title: 'Children of Men', year: 2006, score: 86, reason: "Dystopian future rendered with <span class='hl'>painterly cinematography</span> and grounded human stakes.", cf: 82, sent: 88 },
      { title: 'Stalker', year: 1979, score: 84, reason: "Tarkovsky's meditative pacing and <span class='hl'>spiritual sci-fi</span> influenced the entire genre 2049 inherits from.", cf: 79, sent: 90 },
    ],
  },
  Parasite: {
    meta: { genre: 'thriller · dark comedy', mood: 'tense', runtime: '2h 12m' },
    recs: [
      { title: 'Burning', year: 2018, score: 93, reason: "Korean cinema's masterclass in <span class='hl'>class tension and slow-burn dread</span>, building toward devastating release.", cf: 90, sent: 91 },
      { title: 'Shoplifters', year: 2018, score: 90, reason: "Kore-eda's empathetic study of <span class='hl'>chosen family and economic precarity</span> at the margins.", cf: 87, sent: 89 },
      { title: 'The Lighthouse', year: 2019, score: 87, reason: "Two-hander psychological descent with <span class='hl'>genre-shifting tonal control</span>.", cf: 81, sent: 85 },
      { title: 'Snowpiercer', year: 2013, score: 86, reason: "Bong Joon-ho's earlier <span class='hl'>class-warfare allegory</span> with the same surgical satirical edge.", cf: 88, sent: 83 },
      { title: 'Triangle of Sadness', year: 2022, score: 82, reason: "Ruben Östlund's <span class='hl'>satirical takedown of wealth</span> shares Parasite's gleeful cruelty.", cf: 78, sent: 84 },
    ],
  },
  Stalker: {
    meta: { genre: 'sci-fi · arthouse', mood: 'meditative', runtime: '2h 41m' },
    recs: [
      { title: 'Solaris', year: 1972, score: 96, reason: "Tarkovsky's own companion piece — <span class='hl'>same director, same metaphysical sci-fi grammar</span>.", cf: 94, sent: 95 },
      { title: 'The Mirror', year: 1975, score: 91, reason: "Tarkovsky's most personal film, sharing Stalker's <span class='hl'>dreamlike non-linear poetry</span>.", cf: 92, sent: 88 },
      { title: 'Werckmeister Harmonies', year: 2000, score: 88, reason: "Béla Tarr's <span class='hl'>long-take philosophical cinema</span> directly descends from Tarkovsky's lineage.", cf: 84, sent: 87 },
      { title: 'Sátántangó', year: 1994, score: 85, reason: "A 7-hour meditation on collapse — <span class='hl'>patience as cinematic virtue</span>.", cf: 79, sent: 86 },
      { title: 'Uncle Boonmee', year: 2010, score: 82, reason: "Apichatpong Weerasethakul's <span class='hl'>spiritual slow cinema</span> shares Stalker's mystical undertow.", cf: 76, sent: 84 },
    ],
  },
  'Pulp Fiction': {
    meta: { genre: 'crime · dark comedy', mood: 'stylized', runtime: '2h 34m' },
    recs: [
      { title: 'Reservoir Dogs', year: 1992, score: 95, reason: "Tarantino's debut shares the same <span class='hl'>non-linear narrative and dialogue-driven crime</span> DNA.", cf: 93, sent: 92 },
      { title: 'Jackie Brown', year: 1997, score: 89, reason: "Tarantino's most mature work, with similar <span class='hl'>chapter structure and lived-in characters</span>.", cf: 91, sent: 86 },
      { title: 'Trainspotting', year: 1996, score: 87, reason: "Danny Boyle's kinetic, <span class='hl'>music-driven '90s urban energy</span> — Pulp Fiction's UK cousin.", cf: 84, sent: 88 },
      { title: 'Snatch', year: 2000, score: 84, reason: "Guy Ritchie's <span class='hl'>interlocking crime vignettes</span> owe everything to Pulp Fiction's template.", cf: 82, sent: 83 },
      { title: 'Burn After Reading', year: 2008, score: 81, reason: "Coen Brothers' <span class='hl'>tonal whiplash between violence and absurdity</span>.", cf: 78, sent: 82 },
    ],
  },
  'Spirited Away': {
    meta: { genre: 'animation · fantasy', mood: 'wondrous', runtime: '2h 5m' },
    recs: [
      { title: 'Princess Mononoke', year: 1997, score: 95, reason: "Miyazaki's earlier eco-fantasy with the same <span class='hl'>animism and ethical ambiguity</span>.", cf: 96, sent: 93 },
      { title: 'My Neighbor Totoro', year: 1988, score: 92, reason: "Studio Ghibli's <span class='hl'>gentle magic and child's-eye wonder</span>.", cf: 94, sent: 90 },
      { title: "Howl's Moving Castle", year: 2004, score: 90, reason: "Miyazaki's whimsical world-building and <span class='hl'>transformation as identity metaphor</span>.", cf: 91, sent: 88 },
      { title: 'The Tale of Princess Kaguya', year: 2013, score: 86, reason: "Isao Takahata's <span class='hl'>watercolor folklore</span> shares Ghibli's spiritual depth.", cf: 83, sent: 87 },
      { title: 'Wolf Children', year: 2012, score: 83, reason: "Mamoru Hosoda's <span class='hl'>family fantasy with Miyazaki-adjacent warmth</span>.", cf: 81, sent: 84 },
    ],
  },
  'The Master': {
    meta: { genre: 'drama · psychological', mood: 'unsettling', runtime: '2h 18m' },
    recs: [
      { title: 'There Will Be Blood', year: 2007, score: 96, reason: "PT Anderson's earlier two-hander on <span class='hl'>power, obsession, and male psychology</span>.", cf: 95, sent: 94 },
      { title: 'Phantom Thread', year: 2017, score: 92, reason: "Anderson and Daniel Day-Lewis again, exploring <span class='hl'>control and codependency</span> in confined relationships.", cf: 93, sent: 89 },
      { title: 'Magnolia', year: 1999, score: 88, reason: "PT Anderson's <span class='hl'>operatic American melancholy</span> and damaged-men ensemble.", cf: 90, sent: 85 },
      { title: 'The Brutalist', year: 2024, score: 86, reason: "Brady Corbet's <span class='hl'>post-war epic of obsession and the cost of vision</span>.", cf: 82, sent: 88 },
      { title: 'Inherent Vice', year: 2014, score: 81, reason: "PT Anderson's hazy, <span class='hl'>elliptical character study</span> from the same period.", cf: 84, sent: 79 },
    ],
  },
};

export const demoMovieTitles = Object.keys(demoData);
