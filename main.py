import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import matplotlib.pyplot as plt

# Configurações do OAuth Spotify
SPOTIFY_CLIENT_ID = "SEU_CLIENT_ID"  # Substitua pelo seu Client ID
SPOTIFY_CLIENT_SECRET = "SEU_CLIENT_SECRET"  # Substitua pelo seu Client Secret
SPOTIFY_REDIRECT_URI = "http://localhost:8501"  # Certifique-se de usar este Redirect URI
SCOPE = "user-top-read"  # Escopo necessário para acessar músicas mais ouvidas do usuário

st.set_page_config(page_title="Spotify Analytics", layout="wide")


# Função para autenticar o usuário e acessar a API Spotify
def authenticate_spotify():
    """
    Autentica e cria um cliente Spotify usando Authorization Code Flow.
    """
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True  # Sempre mostrar a janela de login para novos usuários
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


# Função para buscar as 10 músicas mais ouvidas do usuário
def get_user_top_tracks(sp):
    """
    Retorna um DataFrame das 10 músicas mais ouvidas pelo usuário, incluindo:
    - Nome da música
    - Artista(s) principal(is)
    - Popularidade da música
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

        df = pd.DataFrame(track_data)
        return df

    except Exception as e:
        st.error(f"Erro ao acessar a API do Spotify: {e}")
        return pd.DataFrame()


# Função para plotar um gráfico de pizza com as músicas mais ouvidas
def plot_pie_chart(df):
    """
    Gera um gráfico de pizza baseado na popularidade das músicas mais ouvidas.
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


# Configuração do estado da sessão para armazenar dados individuais
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "spotify_client" not in st.session_state:
    st.session_state["spotify_client"] = None


# Função principal da aplicação
def main():
    st.title("🎶 Spotify Analytics")
    st.write(
        "💻 Uma ferramenta que permite múltiplos usuários visualizar suas próprias músicas mais ouvidas no Spotify.")

    # Autenticação condicional com o Spotify
    if not st.session_state["authenticated"]:
        with st.spinner("Aguardando autenticação..."):
            try:
                sp = authenticate_spotify()
                st.session_state["spotify_client"] = sp
                st.session_state["authenticated"] = True
                st.success("✅ Autenticado com sucesso!")
                st.query_params  # Remove parâmetros extras da URL
            except Exception as e:
                st.error("Erro na autenticação. Por favor, tente novamente.")
                st.error(str(e))
                return
    else:
        sp = st.session_state["spotify_client"]

    # Buscar informações do usuário autenticado
    try:
        user_info = sp.current_user()
        st.write(f"👤 **Usuário autenticado como:** {user_info['display_name']}")
        st.write(f"📧 **Email:** {user_info.get('email', 'Email não disponível')}")
    except Exception as e:
        st.error("Erro ao buscar informações do usuário.")
        st.error(str(e))
        return

    # Buscar Top Tracks do usuário
    st.subheader("🎵 Suas Músicas Mais Ouvidas (últimos 30 dias)")
    with st.spinner("Buscando suas músicas mais ouvidas... 🎧"):
        top_tracks_df = get_user_top_tracks(sp)

    # Exibir as músicas em um dataframe
    if not top_tracks_df.empty:
        st.write("Aqui estão suas músicas mais ouvidas:")
        st.dataframe(top_tracks_df, use_container_width=True)

        # Gráfico de pizza baseado na popularidade das músicas
        st.subheader("📊 Popularidade das Top 10 Músicas")
        plot_pie_chart(top_tracks_df)
    else:
        st.warning("⚠️ Parece que você não tem um histórico de músicas mais ouvidas recentemente.")

    # Dar a opção de logout
    if st.button("🔒 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.warning("Você foi desconectado! Atualize a página para realizar o login novamente.")


# Executando a aplicação
if __name__ == "__main__":
    main()
