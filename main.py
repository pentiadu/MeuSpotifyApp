import streamlit as st
import pandas as pd
import os
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import matplotlib.pyplot as plt

st.set_page_config(page_title="Spotify Analytics", layout="wide")

# Configuração OAuth do Spotify
SPOTIFY_CLIENT_ID = "SEU_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "SEU_CLIENT_SECRET"
SPOTIFY_REDIRECT_URI = "http://localhost:8501"  # Verifique se é o redirect correto

scope = "user-top-read"  # Permissão para acessar as músicas mais ouvidas


# Função para autenticação no Spotify
def authenticate_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope
    ))


# Função para recuperar as músicas principais do Spotify
def get_top_tracks(sp):
    """
    Recupera as 10 músicas preferidas do usuário no Spotify
    e retorna as informações em um DataFrame.
    """
    try:
        # Obtém as 10 músicas mais ouvidas do Spotify
        top_tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
        track_data = []  # Lista para armazenar as músicas atuais

        # Extrai as informações de cada música
        for track in top_tracks["items"]:
            track_name = track["name"]
            artist_names = ", ".join([artist["name"] for artist in track["artists"]])
            popularity = track["popularity"]

            # Adiciona os dados numa lista temporária
            track_data.append({
                "Música": track_name,
                "Artista": artist_names,
                "Popularidade": popularity
            })

        # Transforma os dados em um DataFrame
        df_tracks = pd.DataFrame(track_data)

        # Ordena o DataFrame por Popularidade em ordem decrescente
        df_tracks = df_tracks.sort_values(by="Popularidade", ascending=False)

        return df_tracks

    except Exception as e:
        st.error("❌ Houve um erro ao obter as músicas do Spotify.")
        st.error(f"Erro: {str(e)}")
        return pd.DataFrame()


# Função para gerar o gráfico de pizza
def plot_pie_chart(df_tracks):
    """
    Gera um gráfico de pizza com base na popularidade das músicas.
    """
    plt.figure(figsize=(8, 6))
    # Cria uma lista de rótulos no formato "Música - Artista"
    labels = df_tracks.apply(lambda row: f"{row['Música']} - {row['Artista']}", axis=1)
    # Gráfico de Pizza baseado na Popularidade
    plt.pie(
        df_tracks["Popularidade"],
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 8}  # Ajusta o tamanho do texto
    )
    plt.title("Distribuição de Popularidade das Músicas")
    st.pyplot(plt)  # Renderiza o gráfico no Streamlit


# Função de Logout
def logout():
    """Realiza logout no app removendo informações da sessão."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()


# Main do aplicativo Streamlit
def main():
    # Checa se há autenticação na sessão
    authenticated = st.session_state.get("authenticated", False)

    if not authenticated:
        st.title("🎶 Spotify Analytics")
        st.write("Acompanhe suas músicas mais ouvidas diretamente do Spotify!")

        # Botão para autenticação
        if st.button("🔑 Conectar ao Spotify"):
            try:
                sp = authenticate_spotify()
                st.session_state.sp = sp
                st.session_state.authenticated = True
                st.success("✅ Autenticação realizada com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error("❌ Falha na autenticação. Verifique suas credenciais e tente novamente.")
    else:
        sp = st.session_state.sp
        st.title("🎵 Músicas Mais Ouvidas")

        # Exibe informações do usuário conectado
        try:
            user_profile = sp.current_user()
            user_name = user_profile.get("display_name", "Usuário Desconhecido")
            user_email = user_profile.get("email", "Email não disponível")
            st.success(f"👤 Usuário conectado: **{user_name}** ({user_email})")
        except Exception as e:
            st.warning("⚠️ Não foi possível obter informações do usuário.")
            st.warning(str(e))

        # Exibir Top 10 músicas
        with st.spinner("Buscando suas músicas mais ouvidas... 🎧"):
            # Chamar a função principal
            df_tracks = get_top_tracks(sp)

        # Verifica e exibe as músicas
        if df_tracks.empty:
            st.warning("⚠️ Não foram encontradas músicas no histórico do Spotify.")
        else:
            st.subheader("🏆 Suas Músicas Mais Ouvidas (Ordenadas por Popularidade)")
            st.dataframe(df_tracks)  # Aqui a tabela mostrada ao usuário

            # Exibição do gráfico de pizza
            st.subheader("📊 Gráfico de Popularidade das Suas Músicas")
            plot_pie_chart(df_tracks)  # Gera o gráfico

        # Botão de Logout
        st.write("---")
        if st.button("🔒 Logout"):
            logout()


# Executa o app
if __name__ == "__main__":
    main()
