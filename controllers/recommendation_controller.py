from typing import Dict, List, Optional
import streamlit as st
from services.recommendation_service import get_book_recommendations, get_cross_domain_recommendations

class RecommendationController:
    def __init__(self):
        if "book_recommendations" not in st.session_state:
            st.session_state.book_recommendations = None

    def handle_book_recommendations(self, user_input: str) -> Optional[List[Dict]]:
        """Handle book recommendation request"""
        if not user_input:
            st.warning("Please enter your book preferences first!")
            return None

        # Get book recommendations
        recommendations = get_book_recommendations(user_input)
        st.session_state.book_recommendations = recommendations
        return recommendations

    def handle_cross_domain_recommendations(self, selected_index: int) -> Optional[Dict]:
        """Handle cross-domain recommendation request"""
        if not st.session_state.book_recommendations:
            st.error("No book recommendations available")
            return None

        selected_book = st.session_state.book_recommendations[selected_index]
        return get_cross_domain_recommendations(selected_book)