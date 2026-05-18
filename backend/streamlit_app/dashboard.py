"""
CINEIQ Streamlit dashboard.

Three tabs:
  1. Movie explorer — item-item recommendations (works without TMDB)
  2. User explorer  — user-level personalization (requires TMDB)
  3. Taste profile  — top genres/cast/directors for a user (requires TMDB)

Run with:
    streamlit run streamlit_app/dashboard.py
"""
from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from cineiq.data.loader import ML100K_GENRES, load_dataset
from cineiq.models.hybrid import HybridEngine
from cineiq.sentiment.reranker import SentimentReRanker
from cineiq.explain.templates import explain


st.set_page_config(page_title="CINEIQ · Dashboard", layout="wide")


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading dataset and fitting item-item models...")
def get_engine():
    dataset = load_dataset()
    engine = HybridEngine().fit(dataset)
    reranker = SentimentReRanker()
    title_lookup = dict(
        zip(dataset.movies["movie_id"].astype(int),
            dataset.movies["title"].astype(str))
    )
    return dataset, engine, reranker, title_lookup


@st.cache_resource(show_spinner="Loading TMDB and fitting personal models...")
def get_personal_models():
    """Tries to load personal models; returns None if TMDB isn't available."""
    try:
        from cineiq.data.enriched import load_enriched
        from cineiq.models.content_personal import PersonalContentModel
        from cineiq.models.collaborative_personal import PersonalCollaborativeModel
        from cineiq.explain.taste_profile import TasteProfiler

        enriched = load_enriched()
        ds = load_dataset()
        return {
            "enriched": enriched,
            "content": PersonalContentModel().fit(enriched),
            "collab": PersonalCollaborativeModel().fit(ds),
            "profiler": TasteProfiler().fit(),
        }
    except FileNotFoundError as e:
        return None


dataset, engine, reranker, title_lookup = get_engine()
personal = get_personal_models()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("# CINEIQ · Taste Dashboard")
caption = f"{dataset.n_movies:,} movies · {dataset.n_ratings:,} ratings · {dataset.n_users:,} users"
if personal is None:
    caption += "  ·  ⚠️  personal models offline (TMDB not loaded)"
else:
    caption += "  ·  ✅ personal models loaded"
st.caption(caption)

st.divider()


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_movie, tab_user_recs, tab_user_profile = st.tabs([
    "Movie explorer",
    "User recommendations",
    "User taste profile",
])


# ===========================================================================
# Tab 1 — Movie explorer (item-item)
# ===========================================================================

with tab_movie:
    st.subheader("Movie explorer · item-item recommendations")

    c1, c2 = st.columns([3, 1])
    with c1:
        title_query = st.text_input(
            "Seed movie title",
            value="Star Wars (1977)",
            help="Type a substring; pick from the dropdown below.",
            key="movie_query",
        )
    with c2:
        top_n = st.slider("How many?", 3, 20, 8, key="movie_topn")

    matches = dataset.search_titles(title_query, limit=10) if title_query else pd.DataFrame()
    if matches.empty:
        st.warning("No matches. Try another query.")
    else:
        picked_title = st.selectbox(
            "Pick an exact title",
            matches["title"].tolist(),
            index=0,
            key="movie_pick",
        )
        movie_id = int(matches.loc[matches["title"] == picked_title, "movie_id"].iloc[0])

        candidates = reranker.rerank(engine.similar_to(movie_id, top_n=max(50, top_n * 5)))[:top_n]
        movies_idx = dataset.movies.set_index("movie_id")

        st.markdown(f"**Top {len(candidates)} recommendations for** _{picked_title}_:")

        for c in candidates:
            row = movies_idx.loc[c.movie_id]
            ex = explain(movie_id, c, engine.content, title_lookup)
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"### {row['title']}")
                    st.caption(f"{row['genres']}  ·  score: {c.score:.3f}")
                    st.markdown(ex.reason, unsafe_allow_html=True)
                with right:
                    sig_df = pd.DataFrame(
                        {"signal": list(c.components.keys()),
                         "value": list(c.components.values())}
                    )
                    if not sig_df.empty:
                        st.bar_chart(sig_df.set_index("signal"))

        # Genre radar from these recs
        st.divider()
        st.subheader("Genre radar of these recommendations")
        genre_counts = Counter()
        for c in candidates:
            for g in str(movies_idx.loc[c.movie_id, "genres"]).split():
                if g in ML100K_GENRES:
                    genre_counts[g] += 1

        if genre_counts:
            labels = [g for g in ML100K_GENRES if g != "unknown"]
            values = [genre_counts.get(g, 0) for g in labels]
            fig = go.Figure(go.Scatterpolar(r=values, theta=labels, fill="toself"))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# Tab 2 — User recommendations
# ===========================================================================

with tab_user_recs:
    st.subheader("User recommendations · personalized")

    if personal is None:
        st.warning(
            "Personal models are not loaded. Run "
            "`python -m cineiq.data.download_tmdb` and restart this dashboard."
        )
    else:
        # Pick a user — show ones with enough ratings to make sense
        rating_counts = dataset.ratings.groupby("user_id").size().sort_values(ascending=False)
        active_users = rating_counts[rating_counts >= 20].index.tolist()[:200]

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            user_id = st.selectbox(
                "Pick a user",
                active_users,
                key="user_recs_pick",
                help="Users shown have ≥20 ratings",
            )
        with c2:
            strategy = st.selectbox(
                "Strategy",
                ["content", "collab", "hybrid"],
                index=2,
                key="user_recs_strategy",
            )
        with c3:
            top_n_p = st.slider("How many?", 3, 20, 10, key="user_recs_topn")

        # Generate recs
        if strategy == "content":
            recs = personal["content"].recommend_for_user(user_id, top_n=top_n_p)
            df_recs = pd.DataFrame([
                {"movie_id": r.movie_id, "title": r.title, "score": round(r.score, 3)}
                for r in recs
            ])
        elif strategy == "collab":
            recs = personal["collab"].recommend_for_user(user_id, top_n=top_n_p)
            df_recs = pd.DataFrame([
                {
                    "movie_id": r.movie_id,
                    "title": r.title,
                    "pred_rating": round(r.pred_rating, 2),
                    "avg_rating": round(r.avg_rating, 2),
                    "rating_count": r.rating_count,
                }
                for r in recs
            ])
        else:  # hybrid
            c_recs = {r.movie_id: r for r in personal["content"].recommend_for_user(user_id, top_n=top_n_p * 2)}
            cf_recs = {r.movie_id: r for r in personal["collab"].recommend_for_user(user_id, top_n=top_n_p * 2)}
            ids = set(c_recs) | set(cf_recs)
            rows = []
            for mid in ids:
                content_s = c_recs[mid].score if mid in c_recs else 0.0
                collab_s = (cf_recs[mid].pred_rating / 5.0) if mid in cf_recs else 0.0
                title = (c_recs.get(mid) or cf_recs.get(mid)).title
                rows.append({
                    "movie_id": mid,
                    "title": title,
                    "content_score": round(content_s, 3),
                    "collab_score": round(collab_s, 3),
                    "combined": round(0.5 * content_s + 0.5 * collab_s, 3),
                })
            df_recs = pd.DataFrame(rows).sort_values("combined", ascending=False).head(top_n_p)

        if df_recs.empty:
            st.info(f"No recommendations available for user {user_id}.")
        else:
            st.dataframe(df_recs, use_container_width=True, hide_index=True)


# ===========================================================================
# Tab 3 — User taste profile
# ===========================================================================

with tab_user_profile:
    st.subheader("User taste profile · what makes this user tick")

    if personal is None:
        st.warning(
            "Personal models are not loaded. Run "
            "`python -m cineiq.data.download_tmdb` and restart this dashboard."
        )
    else:
        rating_counts = dataset.ratings.groupby("user_id").size().sort_values(ascending=False)
        active_users = rating_counts[rating_counts >= 20].index.tolist()[:200]
        user_id_p = st.selectbox("Pick a user", active_users, key="user_profile_pick")

        profile = personal["profiler"].profile(user_id_p, dataset.ratings)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Top genres")
            if profile.top_genres:
                df = pd.DataFrame(profile.top_genres, columns=["genre", "weight"])
                fig = px.bar(df, x="weight", y="genre", orientation="h", height=320)
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data.")

            st.markdown("### Top directors")
            if profile.top_directors:
                st.dataframe(
                    pd.DataFrame(profile.top_directors, columns=["director", "weight"]),
                    use_container_width=True, hide_index=True,
                )

        with col2:
            st.markdown("### Top cast")
            if profile.top_cast:
                st.dataframe(
                    pd.DataFrame(profile.top_cast, columns=["actor", "weight"]),
                    use_container_width=True, hide_index=True,
                )

            st.markdown("### Top keywords")
            if profile.top_keywords:
                st.dataframe(
                    pd.DataFrame(profile.top_keywords, columns=["keyword", "weight"]),
                    use_container_width=True, hide_index=True,
                )

        st.divider()
        st.markdown("### Top production companies")
        if profile.top_production:
            st.dataframe(
                pd.DataFrame(profile.top_production, columns=["company", "weight"]),
                use_container_width=True, hide_index=True,
            )
