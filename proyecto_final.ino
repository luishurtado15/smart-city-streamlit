#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>
#include <HTTPClient.h>
 
// ——— Configuración Wi-Fi —————————————————————————————————
//const char* ssid     = "Camilo";
//const char* password = "donpapi15"; IP: http://192.168.43.64
 


// ——— Pines de sensores ————————————————————
#define SENSOR_LIGHT_LEFT    12  
#define SENSOR_LIGHT_RIGHT    13
#define SENSOR_CO2    14
#define SENSOR_CNY1    42
#define SENSOR_CNY2    41
#define SENSOR_CNY3    40
#define SENSOR_CNY4    39
#define SENSOR_CNY5    38
#define SENSOR_CNY6    37
#define SENSOR_P1    1
#define SENSOR_P2    2
 
// ——— Pines de actuadores ————————————————————
#define LED_1_RED   5  
#define LED_1_YELLOW   4
#define LED_1_GREEEN   6
#define LED_2_RED   7  
#define LED_2_YELLOW   15
#define LED_2_GREEEN   16
 
// ——— Servidor HTTP ——————————————————————————————————————
WebServer server(80);
 
// ——— Variables de estado —————————————————————————————————
int actual_SENSOR_LIGHT_LEFT = 0;
int actual_SENSOR_LIGHT_RIGHT = 0;
int actual_SENSOR_CO2 = 0;
int actual_SENSOR_CNY1 = 0;
int actual_SENSOR_CNY2 = 0;
int actual_SENSOR_CNY3 = 0;
int actual_SENSOR_CNY4 = 0;
int actual_SENSOR_CNY5 = 0;
int actual_SENSOR_CNY6 = 0;
int actual_SENSOR_P1 = 0;
int actual_SENSOR_P2 = 0;
 
int actuatorState = 0;
 
// ——— Variables ciclo semáforo —————————————————————
 
unsigned long TParpadeo = 500; // Constante para el tiempo de parpadeo de 500ms
unsigned long TRojo = 2000;
unsigned long TVerde = 5000;
unsigned long TAmarillo = 1000;
 
unsigned long tini, tact, trel;
 
bool vR1,vA1,vV1,vR2,vA2,vV2 = 0;
int estado = 0;
int p = 0;
// Variables Clima
const String lat = "6.2001218";
const String lon = "-75.5806761";
float lluvia = 0, viento = 0;
unsigned long tiempoCambio = 0;
unsigned long tiempoAnteriorClima = 0;
const long intervaloClima = 60000;

// LCD
LiquidCrystal_I2C lcd(0x27, 16, 2);
 
// ——— Funciones de manejo de rutas —————————————————————
 
void handleGetSensor() {
 
  actual_SENSOR_LIGHT_LEFT = analogRead(SENSOR_LIGHT_LEFT);
  actual_SENSOR_LIGHT_RIGHT = analogRead(SENSOR_LIGHT_RIGHT);
  actual_SENSOR_CO2 = analogRead(SENSOR_CO2);
  actual_SENSOR_CNY1 = digitalRead(SENSOR_CNY1);
  actual_SENSOR_CNY2 = digitalRead(SENSOR_CNY2);
  actual_SENSOR_CNY3 = digitalRead(SENSOR_CNY3);
  actual_SENSOR_CNY4 = digitalRead(SENSOR_CNY4);
  actual_SENSOR_CNY5 = digitalRead(SENSOR_CNY5);
  actual_SENSOR_CNY6 = digitalRead(SENSOR_CNY6);
  actual_SENSOR_P1 = digitalRead(SENSOR_P1);
  actual_SENSOR_P2 = digitalRead(SENSOR_P2);
 
  // Construir respuesta JSON
  StaticJsonDocument<200> doc;
  doc["SENSOR_LIGHT_LEFT"] = actual_SENSOR_LIGHT_LEFT;
  doc["SENSOR_LIGHT_RIGHT"] = actual_SENSOR_LIGHT_RIGHT;
  doc["SENSOR_CO2"] = actual_SENSOR_CO2;
  doc["SENSOR_CNY1"] = actual_SENSOR_CNY1;
  doc["SENSOR_CNY2"] = actual_SENSOR_CNY2;
  doc["SENSOR_CNY3"] = actual_SENSOR_CNY3;
  doc["SENSOR_CNY4"] = actual_SENSOR_CNY4;
  doc["SENSOR_CNY5"] = actual_SENSOR_CNY5;
  doc["SENSOR_CNY6"] = actual_SENSOR_CNY6;
  doc["SENSOR_P1"] = actual_SENSOR_P1;
  doc["SENSOR_P2"] = actual_SENSOR_P2;
  doc["WIND_SPEED"] = viento;
  doc["PRECIPITATION"] = lluvia;
 
  String out;
  serializeJson(doc, out);
 
  server.send(200, "application/json", out);
}
 
void handlePostActuator() {
  // Leemos el body JSON
  if (server.hasArg("plain") == false) {
    server.send(400, "application/json", "{\"error\":\"Body missing\"}");
    return;
  }
 
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "application/json", "{\"error\":\"JSON invalid\"}");
    return;
  }
 
  // Esperamos { "state": true } o { "state": false }
  if (!doc.containsKey("state")) {
    server.send(422, "application/json", "{\"error\":\"Field 'state' missing\"}");
    return;
  }
 
  actuatorState = doc["state"];
  //digitalWrite(LED_1_RED, actuatorState ? HIGH : LOW);
 
  // Devolver estado actual
  StaticJsonDocument<100> resp;
  resp["status"] = actuatorState;
  String out;
  serializeJson(resp, out);
  actualizarPantalla(actuatorState);
  server.send(200, "application/json", out);
}
 
void handleNotFound(){
  server.send(404, "text/plain", "Not Found");
}
 
// ——— Setup —————————————————————————————————————————————
void setup(){
  Serial.begin(115200);
 
  pinMode(SENSOR_LIGHT_LEFT, INPUT);
  pinMode(SENSOR_LIGHT_RIGHT, INPUT);
  pinMode(SENSOR_CO2, INPUT);
  pinMode(SENSOR_CNY1, INPUT);
  pinMode(SENSOR_CNY2, INPUT);
  pinMode(SENSOR_CNY3, INPUT);
  pinMode(SENSOR_CNY4, INPUT);
  pinMode(SENSOR_CNY5, INPUT);
  pinMode(SENSOR_CNY6, INPUT);
  pinMode(SENSOR_P1, INPUT);
  pinMode(SENSOR_P2, INPUT);
 
  pinMode(LED_1_RED, OUTPUT);
  pinMode(LED_1_YELLOW, OUTPUT);
  pinMode(LED_1_GREEEN, OUTPUT);
  pinMode(LED_2_RED, OUTPUT);
  pinMode(LED_2_YELLOW, OUTPUT);
  pinMode(LED_2_GREEEN, OUTPUT);
  digitalWrite(LED_1_RED, LOW);
  digitalWrite(LED_1_YELLOW, LOW);
  digitalWrite(LED_1_GREEEN, LOW);
  digitalWrite(LED_2_RED, LOW);
  digitalWrite(LED_2_YELLOW, LOW);
  digitalWrite(LED_2_GREEEN, LOW);

  lcd.init(); lcd.backlight(); lcd.clear();
  lcd.print("***ESTADO NORMAL***");

 
  tini = millis(); // Iniciamos la marca de tiempo
 
  // Conectar al Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print(" → Conectado. IP: ");
  Serial.println(WiFi.localIP());
 
  // Rutas HTTP
  server.on("/sensor", HTTP_GET,  handleGetSensor);
  server.on("/actuator", HTTP_POST, handlePostActuator);
  server.onNotFound(handleNotFound);
 
  server.begin();
  Serial.println("Servidor HTTP iniciado en puerto 80");
}
 
// ——— Loop ——————————————————————————————————————————————
void loop(){
  server.handleClient();
 
  actuatorStateCases(actuatorState);
  //sendSensorData();
  getWeather();
 
}
 
void actuatorStateCases(int mode) {
  tact = millis();
  trel = tact-tini;
 
  if(mode == 0){
 
    switch(estado){
      case 0:
        vR1 = 1;
        vA1 = 0;
        vV1 = 0;
        vR2 = 0;
        vA2 = 0;
        vV2 = 1;
 
        if((trel>TVerde)&&(p==0)){
          estado = 4;
          tini = millis();
          p = 1;
        }else if ((trel>TParpadeo)&&(p!=0)){
          estado = 4;
          tini = millis();
          p ++;
        }
        break;
      case 1:
        vR1 = 0;
        vA1 = 1;
        vV1 = 0;
        vR2 = 1;
        vA2 = 0;
        vV2 = 0;
        if(trel>TAmarillo){
          estado = 0;
          tini = millis();
          p = 0;
        }
        break;
      case 2:
        vR1 = 0;
        vA1 = 0;
        vV1 = 1;
        vR2 = 1;
        vA2 = 0;
        vV2 = 0;
        if((trel>TVerde)&&(p==0)){
          estado = 3;
          tini = millis();
          p = 1;
        }else if ((trel>TParpadeo)&&(p!=0)){
          estado = 3;
          tini = millis();
          p ++;
        }
        break;
      case 3:
        vR1 = 0;
        vA1 = 0;
        vV1 = 0;
        vR2 = 1;
        vA2 = 0;
        vV2 = 0;
        if((trel>TParpadeo)&&(p<5)){
          estado = 2;
          tini = millis();
        }else if ((trel>TParpadeo)&&(p==5)){
          estado = 1;
          tini = millis();
        }
        break;
      case 4:
        vR1 = 1;
        vA1 = 0;
        vV1 = 0;
        vR2 = 0;
        vA2 = 0;
        vV2 = 0;
        if((trel>TParpadeo)&&(p<5)){
          estado = 0;
          tini = millis();
        }else if ((trel>TParpadeo)&&(p==5)){
          estado = 5;
          tini = millis();
        }
        break;
      case 5:
        vR1 = 1;
        vA1 = 0;
        vV1 = 0;
        vR2 = 0;
        vA2 = 1;
        vV2 = 0;
        if(trel>TAmarillo){
          estado = 2;
          tini = millis();
          p = 0;
        }
        break;
  }
  }else{
        vR1 = 0;
        vV1 = 0;
        vR2 = 0;
        vV2 = 0;
        if((trel>TParpadeo) ){
          if(vA1==1){
            vA1 = 0;
            vA2 = 0;
          }else{
            vA1 = 1;
            vA2 = 1;
          }
          tini = millis();
        }
  }
 
 
 
  //// ACTUAMOS
  digitalWrite(LED_1_RED,vR1);
  digitalWrite(LED_1_YELLOW,vA1);
  digitalWrite(LED_1_GREEEN,vV1);
  digitalWrite(LED_2_RED,vR2);
  digitalWrite(LED_2_YELLOW,vA2);
  digitalWrite(LED_2_GREEEN,vV2);
 
} 


// Actualizar pantalla
void actualizarPantalla(int mode){
  lcd.clear();
  switch(mode){
    case 0 : lcd.print("***ESTADO NORMAL***");
             Serial.println("ESTADO NORMAL");
             break;
    case 1 : lcd.print("*ESTADO EMERGENCIA*");
             Serial.println("ESTADO EMERGENCIA");
             break;
  }
}


void sendSensorData(){
  HTTPClient http;
  http.begin("http://192.168.1.2:5002/sensor/data"); // IP de tu PC
  http.addHeader("Content-Type", "application/json");
  
  // Crear JSON con datos de sensores
  StaticJsonDocument<200> doc;
  doc["temperature"] = 25.5;
  doc["humidity"] = 60.2;
  doc["pressure"] = 1013.25;
  doc["sensor_id"] = "ESP32_001";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Response: " + response);
  }
  Serial.println("Comunicación de envio");
  http.end();
  delay(5000);
}

void getWeather(){


  if (millis() - tiempoAnteriorClima > intervaloClima) {
    tiempoAnteriorClima = millis();
    
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      String url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat +
                   "&longitude=" + lon + "&current=wind_speed_10m,precipitation";

      http.begin(url);
      if (http.GET() == 200) {
        String res = http.getString();
        StaticJsonDocument<1024> doc;
        if (!deserializeJson(doc, res)) {
          viento = doc["current"]["wind_speed_10m"];
          lluvia = doc["current"]["precipitation"];
        }
        Serial.println("clima: "+res);
      }
      http.end();
    }
  }
}