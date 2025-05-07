import streamlit as st
import pandas as pd
import requests
import pickle
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load data
with open('movie_data.pkl', 'rb') as file:
    movies, cosine_sim = pickle.load(file)

def get_recommendations(title, cosine_sim=cosine_sim):
    """Get movie recommendations for top 5 movies"""
    idx = movies[movies['title'] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]  # Changed to top 5
    movie_indices = [i[0] for i in sim_scores]
    return movies.iloc[movie_indices][['title', 'movie_id']]

def fetch_poster(movie_id):
    """Fetch movie poster with enhanced error handling"""
    api_key = 'b26305c3e235884f08592eeb6a95857c'  # Replace with your valid API key
    
    # Configure retry strategy
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        poster_path = data.get('poster_path')
        
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error: {errh}\nCheck if movie ID {movie_id} is valid")
        return None
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Connection Error: {errc}\nCheck your internet connection")
        return None
    except requests.exceptions.Timeout as errt:
        st.error(f"Timeout Error: {errt}\nServer response too slow")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request Failed: {e}")
        return None
    except KeyError as ke:
        st.error(f"Key Error: {ke}\nInvalid API response format")
        return None

# Streamlit UI
st.title("Movie Recommendation System")
selected_movie = st.selectbox("Select a movie:", movies['title'].values)

if st.button('Recommend'):
    recommendations = get_recommendations(selected_movie)
    
    if not recommendations.empty:
        st.write("Top 5 recommended movies:")  # Updated header
        
        # Single row with 5 columns
        cols = st.columns(5)
        for col, j in zip(cols, range(5)):
            if j < len(recommendations):
                movie = recommendations.iloc[j]
                poster_url = fetch_poster(movie['movie_id'])
                
                with col:
                    if poster_url:
                        st.image(poster_url, width=130, caption=movie['title'])
                    else:
                        st.write("Poster unavailable")
                        st.write(movie['title'])
    else:
        st.warning("No recommendations found.")