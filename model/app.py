class PredictionSystem:
    def __init__(self, model, monitor):
        self.model = model
        self.monitor = monitor
        self.prediction_cache = {}

    def predict_with_confidence(self, umidade, nutrientes):
        X = self._prepare_features(umidade, nutrientes)

        # Get prediction and probabilities
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]

        confidence = np.max(probabilities) * 100

        # Cache prediction for monitoring
        self._cache_prediction(umidade, nutrientes, prediction, confidence)

        return {
            'acao': prediction,
            'confianca': confidence,
            'probabilidades': dict(zip(self.model.classes_, probabilities))
        }

    def _prepare_features(self, umidade, nutrientes):
        # Prepare features for prediction
        return np.array([[
            umidade / 100.0,
            nutrientes / 10.0
        ]])

    def _cache_prediction(self, umidade, nutrientes, prediction, confidence):
        self.prediction_cache[datetime.now()] = {
            'umidade': umidade,
            'nutrientes': nutrientes,
            'prediction': prediction,
            'confidence': confidence
        }
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
from datetime import datetime
import joblib
from sklearn.tree import DecisionTreeClassifier
import paho.mqtt.client as mqtt
import threading

# Configurações gerais
st.set_page_config(
    page_title="FarmTech Solutions",
    page_icon="🌱",
    layout="wide"
)

# Título principal
st.title("🌱 FarmTech Solutions - Monitoramento Inteligente de Agricultura")
st.markdown("---")

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Visão Geral", 
    "📊 Dados Históricos", 
    "🧪 Simulador", 
    "🤖 IA + MQTT"
])

# Dados históricos
df = pd.read_csv("farmtech_leituras_formatado.csv", encoding='utf-8')

with tab1:  # Visão Geral
    st.header("Visão Geral do Projeto")
    st.markdown("""
    **FarmTech Solutions** é um sistema integrado para agricultura de precisão que combina:
    - Sensores de umidade/nutrientes (ESP32)
    - Display LCD para feedback em tempo real
    - Broker MQTT para comunicação
    - Modelo de IA para decisões de irrigação/adubação
    """)
    
    st.subheader("🔧 Arquitetura do Sistema")
    st.image("https://raw.githubusercontent.com/wokwi/wokwi-elements/main/images/diagram.png", 
             caption="Diagrama do Sistema - Fonte: Wokwi")
    
    st.subheader("⚙️ Fluxo de Dados")
    st.markdown("""
    1. ESP32 lê sensores (potenciômetro simulado)
    2. Dados enviados via MQTT para o broker
    3. Serviço Python consome dados e aplica modelo de IA
    4. Decisões são exibidas no dashboard
    """)
    
    st.subheader("📈 Estatísticas Chave")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Leituras", len(df))
    with col2:
        st.metric("Média Umidade", f"{df['valor_umidade'].mean():.1f}%")
    with col3:
        st.metric("Ações Mais Comuns", df['acao_prevista'].mode()[0])

with tab2:  # Dados Históricos
    st.header("📊 Análise de Dados Históricos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        sensor_id = st.selectbox("Selecione o Sensor", df['id_sensor'].unique())
    with col2:
        acao = st.selectbox("Filtrar por Ação", ['Todas'] + list(df['acao_prevista'].unique()))
    
    # Aplicar filtros
    filtered_df = df[df['id_sensor'] == sensor_id]
    if acao != 'Todas':
        filtered_df = filtered_df[filtered_df['acao_prevista'] == acao]
    
    # Mostrar dados
    st.dataframe(filtered_df.sort_values('timestamp', ascending=False))
    
    # Gráficos
    st.subheader("📈 Tendências ao Longo do Tempo")
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    
    # Gráfico de umidade
    ax[0].plot(filtered_df['timestamp'], filtered_df['valor_umidade'], 'b-o')
    ax[0].axhline(y=40, color='r', linestyle='--', label='Limite Inferior')
    ax[0].axhline(y=70, color='g', linestyle='--', label='Limite Superior')
    ax[0].set_title('Variação de Umidade')
    ax[0].set_ylabel('Umidade (%)')
    ax[0].legend()
    ax[0].tick_params(axis='x', rotation=45)
    
    # Gráfico de nutrientes
    ax[1].bar(filtered_df['timestamp'], filtered_df['valor_nutrientes'], color='orange')
    ax[1].set_title('Níveis de Nutrientes')
    ax[1].set_ylabel('Nutrientes')
    ax[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Distribuição de ações
    st.subheader("📊 Distribuição de Ações Recomendadas")
    action_counts = filtered_df['acao_prevista'].value_counts()
    st.bar_chart(action_counts)

with tab3:  # Simulador
    st.header("🧪 Simulador de Sensores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Controles do simulador
        st.subheader("🔧 Parâmetros do Sensor")
        umidade = st.slider("Umidade do Solo (%)", 0, 100, 45)
        nutrientes = st.slider("Nível de Nutrientes", 0, 10, 5)
        
        # Simular leitura
        if st.button("Enviar Leitura Simulada", key="send_sim"):
            sim_data = {
                "valor_umidade": umidade,
                "valor_nutrientes": nutrientes,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.sim_data = sim_data
            st.success("✅ Dados enviados para processamento!")
    
    with col2:
        # Display LCD simulado
        st.subheader("🖥️ Display LCD (Simulação ESP32)")
        
        # Determinar status
        if umidade < 40:
            status = "Irrigando..."
            status_color = "#FF5555"  # Vermelho
        elif umidade <= 70:
            status = "Solo OK"
            status_color = "#55FF55"  # Verde
        else:
            status = "Encharcado"
            status_color = "#5555FF"  # Azul
        
        # Criar display LCD
        lcd_html = f"""
        <div style="
            background-color: #2c3e50;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            width: 300px;
            margin: 0 auto;
        ">
            <div style="
                background-color: #1a242f;
                border-radius: 5px;
                padding: 15px;
                color: #ecf0f1;
                text-align: center;
            ">
                <div style="font-size: 18px; margin-bottom: 10px;">
                    Umid.: {umidade}%
                </div>
                <div style="
                    font-size: 18px;
                    color: {status_color};
                    font-weight: bold;
                ">
                    {status}
                </div>
            </div>
        </div>
        """
        st.markdown(lcd_html, unsafe_allow_html=True)
    
    # Mostrar dados simulados se existirem
    if 'sim_data' in st.session_state:
        st.subheader("📤 Dados Simulados Enviados")
        st.json(st.session_state.sim_data)

with tab4:  # IA + MQTT
    st.header("🤖 Sistema de Decisão com IA")
    
    # Explicação do modelo
    st.markdown("""
    **Modelo de Machine Learning:**
    - Algoritmo: Árvore de Decisão (Decision Tree)
    - Features: Umidade do solo + Nível de nutrientes
    - Saída: Ação recomendada (Irrigar, Adubar, etc.)
    """)
    
    # Simulação de IA
    st.subheader("🧠 Simulador de Decisão IA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Entradas para simulação
        sim_umidade = st.slider("Umidade (%)", 0, 100, 35, key="ia_umidade")
        sim_nutrientes = st.slider("Nutrientes", 0, 10, 3, key="ia_nutrientes")
    
    with col2:
        # Simular decisão IA (lógica simplificada)
        st.subheader("🎯 Decisão Recomendada")
        
        if sim_umidade < 40 and sim_nutrientes < 4:
            acao = "Irrigar e Adubar"
            cor = "#FF5555"
        elif sim_umidade < 40:
            acao = "Irrigar"
            cor = "#FFAA55"
        elif sim_nutrientes < 4:
            acao = "Adubar"
            cor = "#55AAFF"
        else:
            acao = "Nenhuma ação"
            cor = "#55FF55"
        
        st.markdown(f"""
        <div style="
            background-color: {cor};
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: white;
        ">
            {acao}
        </div>
        """, unsafe_allow_html=True)
    
    # Simulação MQTT
    st.subheader("📡 Simulação de Fluxo MQTT")
    
    if st.button("Iniciar Simulação MQTT", key="start_mqtt"):
        # Criar dados de simulação
        mqtt_messages = [
            {"valor_umidade": 35, "valor_nutrientes": 3},
            {"valor_umidade": 60, "valor_nutrientes": 5},
            {"valor_umidade": 25, "valor_nutrientes": 2},
            {"valor_umidade": 75, "valor_nutrientes": 1}
        ]
        
        placeholder = st.empty()
        
        for i, message in enumerate(mqtt_messages):
            with placeholder.container():
                # Simular recebimento de mensagem
                st.markdown(f"### 📬 Mensagem MQTT Recebida #{i+1}")
                st.json(message)
                
                # Simular processamento IA
                if message["valor_umidade"] < 40 and message["valor_nutrientes"] < 4:
                    decision = "Irrigar e Adubar"
                elif message["valor_umidade"] < 40:
                    decision = "Irrigar"
                elif message["valor_nutrientes"] < 4:
                    decision = "Adubar"
                else:
                    decision = "Nenhuma ação"
                
                st.markdown(f"### 🤖 Decisão IA: `{decision}`")
                
                # Barra de progresso
                progress = st.progress(0)
                for percent in range(100):
                    time.sleep(0.02)
                    progress.progress(percent + 1)
                
                st.markdown("---")
            
            time.sleep(2)

# Rodapé
st.markdown("---")
st.markdown("**FarmTech Solutions** © 2025 | Integração de IoT com IA para Agricultura de Precisão")