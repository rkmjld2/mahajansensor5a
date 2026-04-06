#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>

// -------- WIFI --------
const char* ssid = "Airtel_56";
const char* password = "Raviuma5658";

// -------- SERVER --------
String server = "https://mahajansensor5a.onrender.com";

// -------- API KEY --------
String apiKey = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5";

WiFiClientSecure client;

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected ✅");
}

void setup() {
  Serial.begin(115200);
  connectWiFi();

  // HTTPS fix
  client.setInsecure();
}

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconnecting WiFi...");
    connectWiFi();
    return;
  }

  HTTPClient http;

  // -------- STEP 1: HEARTBEAT --------
  http.begin(client, server + "/ping");
  http.setTimeout(10000);
  int pingCode = http.GET();
  Serial.println("Ping: " + String(pingCode));
  http.end();

  delay(500);

  // -------- STEP 2: SEND DATA --------
  float s1 = random(200, 300);
  float s2 = random(500, 700);
  float s3 = random(300, 600);

  String url = server + "/api/data?key=" + apiKey +
               "&s1=" + String(s1, 2) +
               "&s2=" + String(s2, 2) +
               "&s3=" + String(s3, 2);

  Serial.println("Sending: " + url);

  http.begin(client, url);
  http.setTimeout(15000);

  int httpCode = http.GET();

  if (httpCode > 0) {
    Serial.println("HTTP Code: " + String(httpCode));
    Serial.println("Response: " + http.getString());
  } else {
    Serial.println("❌ Error: " + http.errorToString(httpCode));
  }

  http.end();

  // -------- INTERVAL --------
  delay(5000);   // ✅ 5 sec (stable)
}