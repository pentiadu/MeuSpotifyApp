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


# Função para autenticar e criar uma instância do cliente Spotify
def authenticate_user():
    """
    Realiza a autenticação do usuário no Spotify e retorna um objeto Spotipy autenticado.
    """
    if "token_cache" not in st.session_state:
        st.session_state.token_cache = None  # Inicializa o cache na sessão

    # Configura o SpotifyOAuth com cache específico para cada usuário
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=None,  # Evita salvar cache localmente
    )

    # Sincroniza o cache do SpotifyOAuth com o `st.session_state`
    auth_manager.cache_handler.token_info = st.session_state.token_cache

    if not auth_manager.get_cached_token():
        # Realiza a autenticação caso o token de acesso não esteja no cache
        token = auth_manager.get_access_token(as_dict=False)
        st.session_state.token_cache = auth_manager.cache_handler.token_info

    return spotipy.Spotify(auth_manager=auth_manager)


# Função para recuperar as 10 músicas mais ouvidas do usuário
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


# Função para exibir o gráfico de pizza com base nas músicas mais ouvidas
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


# Função principal
def main():
    st.title("🎶 Spotify Analytics")

    # Verifica se o usuário está autenticado
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Página de login
    if not st.session_state["authenticated"]:
        st.subheader("Bem-vindo ao Spotify Analytics!")
        st.write("Faça login para acessar suas músicas mais ouvidas no Spotify.")
        if st.button("Login com Spotify"):
            try:
                sp = authenticate_user()
                st.session_state["spotify_client"] = sp
                st.session_state["authenticated"] = True
                st.query_params(page="home")  # Atualiza estado para trocar a página
            except Exception as e:
                st.error("Erro durante o processo de login. Tente novamente.")
                st.error(str(e))
        return

    # Exibição dos dados do Spotify
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

    # Buscar músicas mais ouvidas
    st.subheader("🎵 Suas Músicas Mais Ouvidas (últimos 30 dias)")
    top_tracks_df = get_user_top_tracks(sp)

    if not top_tracks_df.empty:
        # Exibe as músicas em uma tabela
        st.dataframe(top_tracks_df, use_container_width=True)

        # Cria um gráfico de pizza
        st.subheader("📊 Popularidade das Top 10 Músicas")
        plot_pie_chart(top_tracks_df)
    else:
        st.warning("⚠️ Você não tem histórico de músicas mais ouvidas para exibir.")

    # Botão de logout
    if st.button("🔒 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.warning(
            "Você foi desconectado! Recarregue a página ou clique [aqui](http://localhost:8501) para voltar ao login.")


# Executa o aplicativo
if __name__ == "__main__":
    main()
