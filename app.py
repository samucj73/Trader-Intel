import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import base64

st.set_page_config(layout="wide", page_title="Roleta Modo Trader")

# Estado inicial
if "numeros" not in st.session_state:
    st.session_state.numeros = []
if "banca" not in st.session_state:
    st.session_state.banca = 0.0
if "meta" not in st.session_state:
    st.session_state.meta = 0.0
if "stop" not in st.session_state:
    st.session_state.stop = 0.0
if "lucro" not in st.session_state:
    st.session_state.lucro = 0.0

# Layout com colunas
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Roleta Modo Trader - Captura Automática e IA")

with col2:
    st.subheader("Gerenciamento de Banca")
    st.session_state.banca = st.number_input("Banca Inicial (R$)", value=st.session_state.banca, step=10.0)
    st.session_state.meta = st.number_input("Meta de Lucro (R$)", value=st.session_state.meta, step=10.0)
    st.session_state.stop = st.number_input("Stop Loss (R$)", value=st.session_state.stop, step=10.0)

st.divider()

# Janela do jogo
st.markdown("### Roleta Betfair ao Vivo")
components.iframe(
    "https://play.betfair.bet.br/launch/mobile?returnURL=https%3A%2F%2Flauncher.betfair.bet.br%2Flauncher%2F%3FgameId%3Dlive-lr-brazil-cev%26channel%3Dy...",
    height=600,
    scrolling=True
)

st.markdown("### Captura Automática (OCR)")
components.html("""
<video id="video" autoplay muted style="width:100%; max-width: 600px; border:1px solid #ccc;"></video>
<canvas id="canvas" style="display:none;"></canvas>
<p id="resultado" style="font-size:16px; font-family: Arial;"></p>
<script src="https://cdn.jsdelivr.net/npm/tesseract.js@4.0.2/dist/tesseract.min.js"></script>
<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const resultado = document.getElementById('resultado');
navigator.mediaDevices.getDisplayMedia({ video: true }).then((stream) => {
    video.srcObject = stream;
    setInterval(() => {
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        Tesseract.recognize(canvas, 'eng', {
            tessedit_char_whitelist: '0123456789 ',
        }).then(({ data: { text } }) => {
            let numeros = text.replace(/[^0-9 ]/g, '').trim();
            window.parent.postMessage(numeros, "*");
            resultado.innerText = "Detectado: " + numeros;
        });
    }, 5000);
});
</script>
""", height=380)
# Receber números automaticamente via postMessage
components.html("""
<script>
window.addEventListener("message", (event) => {
    const numeros = event.data.trim().split(" ").map(n => parseInt(n)).filter(n => !isNaN(n));
    fetch("/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ numeros })
    });
});
</script>
""", height=0)

st.markdown("### Inserir números manualmente (opcional)")
num_input = st.text_input("Digite até 100 números separados por espaço ou vírgula:")

if st.button("Adicionar números"):
    novos = [int(n) for n in num_input.replace(",", " ").split() if n.isdigit()]
    st.session_state.numeros += novos
    st.session_state.numeros = st.session_state.numeros[-100:]  # manter só os 100 últimos

st.info(f"Total de números carregados: {len(st.session_state.numeros)}")

# IA simples baseada em frequência
def prever_proximos_numeros(numeros, qtd=10):
    if not numeros:
        return []
    serie = pd.Series(numeros)
    freq = serie.value_counts().sort_values(ascending=False)
    return freq.head(qtd).index.tolist()

# Estatísticas
if st.session_state.numeros:
    st.subheader("Estatísticas dos Últimos 100 Números")

    df = pd.DataFrame(st.session_state.numeros, columns=["Número"])
    freq = df["Número"].value_counts().sort_index()
    moda = df["Número"].mode()[0]
    media = df["Número"].mean()
    mediana = df["Número"].median()
    desvio = df["Número"].std()

    col3, col4, col5 = st.columns(3)
    col3.metric("Média", round(media, 2))
    col4.metric("Mediana", mediana)
    col5.metric("Moda", moda)

    st.bar_chart(freq)

    st.markdown("### Previsão com IA (Top Frequentes)")
    previsao = prever_proximos_numeros(st.session_state.numeros)
    st.success(f"Possíveis próximos números: {previsao}")
  # Simulação de lucro/prejuízo com base na previsão (exemplo)
st.markdown("### Simulação de Apostas")

aposta_por_numero = st.number_input("Valor por número previsto (R$)", value=2.0, step=1.0)

if st.button("Simular rodada"):
    if previsao:
        ganho = 36 * aposta_por_numero if np.random.choice(previsao) in st.session_state.numeros[-1:] else 0
        gasto = aposta_por_numero * len(previsao)
        resultado = ganho - gasto
        st.session_state.lucro += resultado
        st.metric("Resultado da rodada", f"R$ {resultado:.2f}", delta=f"{st.session_state.lucro:.2f}")

        # Verificar meta ou stop
        if st.session_state.lucro >= st.session_state.meta:
            st.success("Meta diária alcançada!")
        elif abs(st.session_state.lucro) >= st.session_state.stop:
            st.error("Stop loss atingido!")

# Exportações
st.markdown("### Exportações")

def gerar_csv():
    df = pd.DataFrame(st.session_state.numeros, columns=["Número"])
    return df.to_csv(index=False).encode()

def gerar_excel():
    df = pd.DataFrame(st.session_state.numeros, columns=["Número"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    return output.getvalue()

col_export1, col_export2 = st.columns(2)
col_export1.download_button("Baixar CSV", gerar_csv(), file_name="numeros_roleta.csv", mime="text/csv")
col_export2.download_button("Baixar Excel", gerar_excel(), file_name="numeros_roleta.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Reset
if st.button("Resetar Tudo"):
    st.session_state.numeros = []
    st.session_state.lucro = 0.0
    st.success("Dados reiniciados.")
