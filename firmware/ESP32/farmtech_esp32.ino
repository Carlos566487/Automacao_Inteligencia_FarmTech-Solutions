#include <Wire.h> // Biblioteca para comunicação I2C
#include <LiquidCrystal_I2C.h> // Biblioteca do display LCD com interface I2C

// Criação do objeto LCD no endereço padrão 0x27, com 16 colunas e 2 linhas
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Pino analógico do ESP32 que lê o valor do sensor de umidade (potenciômetro)
const int pinUmidade = 34;

// Declaração das variáveis principais
int leituraBruta = 0;        // Armazena a leitura bruta do sensor (0 a 4095)
float umidade = 0.0;         // Umidade convertida para porcentagem (%)
bool irrigando = false;      // Estado lógico da irrigação (true = ligado)

// Função que roda uma vez ao iniciar o ESP32
void setup() {
  Serial.begin(115200); // Inicializa a comunicação Serial com baud rate de 115200

  lcd.init();           // Inicializa o LCD
  lcd.backlight();      // Liga a luz de fundo do display

  // Mensagem de boas-vindas
  lcd.setCursor(0, 0);
  lcd.print("FarmTech Pronto!");
  delay(2000);          // Aguarda 2 segundos
  lcd.clear();          // Limpa a tela
}

// Função principal que roda continuamente
void loop() {
  // Lê o valor analógico do potenciômetro (0 a 4095)
  leituraBruta = analogRead(pinUmidade);

  // Converte a leitura para uma porcentagem de umidade (0% a 100%)
  umidade = map(leituraBruta, 0, 4095, 0, 100);

  // Define se a irrigação deve estar ativada com base na umidade
  irrigando = (umidade < 40);

  // Envia os dados para o Serial Plotter
  Serial.print("Umidade: ");
  Serial.print(umidade);
  Serial.println(" %");

  // Atualiza a primeira linha do display com a umidade
  lcd.setCursor(0, 0);
  lcd.print("Umid.: ");
  lcd.print(umidade, 1); // Mostra a umidade com 1 casa decimal
  lcd.print("%     ");   // Espaço extra para apagar resíduos anteriores

  // Atualiza a segunda linha do display com o status da irrigação
  lcd.setCursor(0, 1);
  if (umidade < 40) {
    lcd.print("Irrigando... "); // Umidade baixa
  } else if (umidade <= 70) {
    lcd.print("Solo OK      "); // Umidade ideal
  } else {
    lcd.print("Encharcado   "); // Umidade muito alta
  }

  delay(1000); // Aguarda 1 segundo antes de repetir o ciclo
}
