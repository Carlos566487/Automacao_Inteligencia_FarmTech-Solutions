import json
import pandas as pd
import joblib
import paho.mqtt.client as mqtt

# Carrega o modelo e o codificador
modelo = joblib.load("modelo_irrigacao.joblib")
label_encoder = joblib.load("label_encoder.joblib")


# Função chamada ao receber mensagem MQTT
def on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        entrada = pd.DataFrame([dados])
        pred = modelo.predict(entrada)
        acao = label_encoder.inverse_transform(pred)

        print(f"[📡 Recebido] {dados}")
        print(f"[🤖 Ação prevista] {acao[0]}")
        print("-" * 40)
    except Exception as e:
        print("[❌ Erro]:", e)


# Configurações do broker Mosquitto
broker = "mqtt-dashboard.com"
topico = "farmtech/leituras"

client = mqtt.Client()
client.on_message = on_message
client.connect(broker, 1883)
client.subscribe(topico)

print(f"✅ Conectado ao broker {broker} - tópico '{topico}'")
client.loop_forever()


