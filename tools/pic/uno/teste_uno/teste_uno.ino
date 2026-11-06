// Teste do Arduino Uno (e clones com CH340): LED da placa pisca, a serial manda um sinal de vida
// por segundo e devolve em eco o que receber. Não mexe em nenhum outro pino.
// Compilar e gravar: ver tools/pic/uno/README.md ("Testar o Uno").
unsigned long ultimo = 0;
unsigned long contador = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  Serial.println(F("TESTE_UNO pronto"));
  Serial.print(F("F_CPU="));
  Serial.println(F_CPU);
}

void loop() {
  if (millis() - ultimo >= 1000) {
    ultimo = millis();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    Serial.print(F("vivo "));
    Serial.println(++contador);
  }
  while (Serial.available()) {
    int c = Serial.read();
    Serial.print(F("eco:"));
    Serial.println((char)c);
  }
}
