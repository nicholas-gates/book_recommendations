import streamlit as st

def display_cross_domain_recommendations(recommendations):
    """Display cross-domain recommendations (movies, games, songs)"""
    if recommendations:
        # Display movie recommendation
        st.subheader("🎬 Movie Recommendation")
        movie = recommendations.get("movie", {})
        st.write(f"**{movie.get('title')} ({movie.get('year')})**")
        st.write(movie.get('description'))
        st.write(f"**Why this movie:** {movie.get('reason')}")

        # Display game recommendation
        st.subheader("🎮 Game Recommendation")
        game = recommendations.get("game", {})
        st.write(f"**{game.get('title')} ({game.get('platform')})**")
        st.write(game.get('description'))
        st.write(f"**Why this game:** {game.get('reason')}")

        # Display song recommendation
        st.subheader("🎵 Song Recommendation")
        song = recommendations.get("song", {})
        st.write(f"**{song.get('title')} by {song.get('artist')}**")
        st.write(song.get('description'))
        st.write(f"**Why this song:** {song.get('reason')}")
    else:
        st.error("Failed to generate cross-domain recommendations. Please try again.")