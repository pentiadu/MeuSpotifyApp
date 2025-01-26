import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import matplotlib.pyplot as plt
import uuid

# Configurações do OAuth Spotify
SPOTIFY_CLIENT_ID = "fa95b32491d048ae9762bf882e9c33c9"  # Substitua pelo seu Client ID
SPOTIFY_CLIENT_SECRET = "7dfc7349c85f44f3b1d6d36cf93c5541"  # Substitua pelo seu Client Secret
SPOTIFY_REDIRECT_URI = "http://localhost:8501"  # Use este Redirect URI no Spotify
SCOPE = "user-top-read"  # Escopo necessário para acessar músicas mais ouvidas do usuário


def get_cache_path_for_user():
    """
    Cria um identificador exclusivo para o token de autenticação do Spotify.
    Isto assegura que múltiplos usuários tenham sessões separadas.
    """
    if "session_id" not in st.session_state:
        # Gera um ID de sessão exclusivo para cada usuário
        st.session_state["session_id"] = str(uuid.uuid4())

    # Cada sessão terá um caminho de cache único
    return f".cache-{st.session_state['session_id']}"


def authenticate_user():
    """
    Realiza a autenticação do usuário no Spotify.
    Cada usuário terá seu próprio cache isolado.
    """
    # Define o caminho do cache específico para a sessão
    cache_path = get_cache_path_for_user()

    # Configura o SpotifyOAuth com o cache exclusivo
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=cache_path,
    )

    # Verifica ou solicita o login
    if not auth_manager.get_cached_token():
        auth_manager.get_access_token(as_dict=False)

    return spotipy.Spotify(auth_manager=auth_manager)


def get_user_top_tracks(sp):
    """
    Retorna um dataframe com as 10 músicas mais ouvidas do usuário, incluindo:
    - Nome da música
    - Artista(s)
    - Popularidade
    """
    try:
        top_tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
        track_data = []
        for track in top_tracks["items"]:
            track_data.append({
                "Música": track["name"],
                "Artista(s)": ", ".join([artist["name"] for artist in track["artists"]]),
                "Popularidade": track["popularity"]
            })
        return pd.DataFrame(track_data)
    except Exception as e:
        st.error(f"Erro ao acessar os dados do Spotify: {e}")
        return pd.DataFrame()


def plot_pie_chart(df):
    """
    Cria um gráfico de pizza com base na popularidade das músicas mais ouvidas.
    """
    plt.figure(figsize=(8, 6))
    labels = df.apply(lambda x: f"{x['Música']} - {x['Artista(s)']}", axis=1)
    plt.pie(
        df["Popularidade"],
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 8}
    )
    plt.title("Popularidade das 10 músicas mais ouvidas")
    st.pyplot(plt)


def clear_cache():
    """
    Remove o cache da sessão atual do usuário, bem como o estado armazenado.
    """
    if "session_id" in st.session_state:
        cache_file = f".cache-{st.session_state['session_id']}"
        try:
            import os
            os.remove(cache_file)  # Remove o cache específico da sessão
        except FileNotFoundError:
            pass
    # Limpa todo o estado da sessão
    st.session_state.clear()


def main():
    # Configura o título do app
    st.title("🎶 Spotify Analytics")

    # Controle de login
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Página de login
    if not st.session_state["authenticated"]:
        st.subheader("Bem-vindo ao Spotify Analytics!")
        st.write("Faça login para acessar suas músicas mais ouvidas no Spotify.")
        if st.button("Login com Spotify"):
            try:
                # Realiza autenticação
                sp = authenticate_user()
                st.session_state["spotify_client"] = sp
                st.session_state["authenticated"] = True
                st.success("Login realizado com sucesso!")
            except Exception as e:
                st.error("Erro durante o processo de login. Tente novamente.")
                st.error(str(e))
        return  # Encerrar execução aqui se o usuário ainda não estiver autenticado

    # Usuário autenticado
    sp = st.session_state["spotify_client"]

    # Exibe dados do usuário conectado
    try:
        user_info = sp.current_user()
        st.success(f"✅ Bem-vindo(a), **{user_info['display_name']}**!")
        st.write(f"📧 **Email:** {user_info.get('email', 'Não disponível')}")
    except Exception as e:
        st.error("Erro ao buscar informações do usuário.")
        st.error(str(e))
        return

    # Buscar e exibir músicas mais ouvidas
    st.subheader("🎵 Suas Músicas Mais Ouvidas (últimos 30 dias)")
    top_tracks_df = get_user_top_tracks(sp)

    if not top_tracks_df.empty:
        st.dataframe(top_tracks_df, use_container_width=True)

        # Gráfico de popularidade
        st.subheader("📊 Popularidade das Top 10 Músicas")
        plot_pie_chart(top_tracks_df)
    else:
        st.warning("⚠️ Você não tem histórico de músicas mais ouvidas para exibir.")

    # Botão de logout
    if st.button("🔒 Logout"):
        clear_cache()
        st.warning("Você foi desconectado! Atualize a página para realizar login novamente.")


if __name__ == "__main__":
    main()
