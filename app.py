import streamlit as st
from auth import requires_auth
from controllers.recommendation_controller import RecommendationController
from views.book_recommendations_view import display_book_recommendations
from views.cross_domain_view import display_cross_domain_recommendations
from utils import logger

@requires_auth
def main():
    logger.info("Starting Book Recommendation System")
    controller = RecommendationController()

    st.title("📚 Book Recommendation System")
    st.write("""
    Welcome to the Book Recommendation System! Tell me what kind of books you're interested in,
    and I'll provide personalized recommendations. You can mention:
    - Authors you enjoy
    - Genres you prefer
    - Themes or topics you're interested in
    - Writing styles you like
    - Or any other criteria!
    """)

    # Get user input
    user_input = st.text_area("What kind of books are you looking for?",
                            placeholder="E.g., 'I love magical realism like Gabriel García Márquez' or 'Looking for sci-fi books about time travel'")

    if st.button("Get Recommendations"):
        recommendations = controller.handle_book_recommendations(user_input)

    # Display book recommendations if available
    if st.session_state.book_recommendations:
        display_book_recommendations(st.session_state.book_recommendations)

        # Add a section for cross-domain recommendations
        st.subheader("Get Cross-Domain Recommendations")
        st.write("Select a book to get related movie, game, and song recommendations that share similar themes.")

        # Create dropdown with book titles
        book_titles = [book["title"] for book in st.session_state.book_recommendations]
        selected_index = st.selectbox(
            "Select a book",
            range(len(book_titles)),
            format_func=lambda i: book_titles[i]
        )

        if st.button("Get Related Content"):
            recommendations = controller.handle_cross_domain_recommendations(selected_index)
            if recommendations:
                display_cross_domain_recommendations(recommendations)

if __name__ == "__main__":
    main()
