from models import BookRecommendation
import streamlit as st

def display_book_recommendations(recommendations):
    """Display book recommendations in a formatted way"""
    for i, book_dict in enumerate(recommendations, 1):
        book = BookRecommendation(**book_dict)
        with st.container():
            st.subheader(f"{i}. {book.title} by {book.author}")
            st.write(f"**Genre:** {book.genre}")
            st.write(f"**Description:** {book.description}")
            st.write(f"**Why this book:** {book.reason}")
            st.divider()