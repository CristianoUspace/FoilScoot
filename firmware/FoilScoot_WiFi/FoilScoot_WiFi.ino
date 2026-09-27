// FoilScoot - Cristiano Baldoni - ESP-WROOM-32 / MPU6050
// Libreria originale MPU6050 inclusa nella cartella src.
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <esp_timer.h>
#include <esp_system.h>
#include <math.h>
#include <ctype.h>
#include "src/MPU6050/MPU6050.h"

constexpr int WARNING_LED = 23, BOARD_LED = 2;
constexpr char SSID[] = "FoilScoot-IMU";
constexpr char PASSWORD[] = "FoilScoot32";
constexpr uint8_t IMU_ADDR = 0x68; // Come MPU6050() nel progetto originale.
constexpr uint32_t SAMPLE_US = 10000; // 100 Hz nominali; ogni misura ha il proprio tempo.
// Attivare SOLO dopo aver collegato e verificato il partitore 22k / 10k.
constexpr bool BATTERY_MONITOR_ENABLED = true;
constexpr int BATTERY_PIN = 34; // ADC1: disponibile anche con Wi-Fi acceso.
constexpr float BATTERY_R_TOP = 22000.0f;
constexpr float BATTERY_R_BOTTOM = 10000.0f;
constexpr float BATTERY_CAL_FACTOR = 1.0f; // V_multimetro / V_client, dopo confronto.
uint32_t batteryLastMs = 0, batterySumMv = 0;
uint8_t batteryCount = 0;
MPU6050 imu(IMU_ADDR);
WiFiServer server(8765);
WiFiClient client;
String command, bootId, sessionId;
bool ready = false, recording = false, stopping = false, greeted = false;
bool wifiOk = false, filtered = false;
String imuError = "NOT_CALIBRATED";
float bias[6] = {}, values[6] = {};
uint64_t nextSample = 0, lastSample = 0, sequence = 0, missed = 0;
uint32_t lastPing = 0, connectBlink = 0;
int syncStep = -1;
uint64_t syncDeadline = 0;
String syncLabel;
bool ledState = false;
const uint32_t SYNC_MS[] = {120, 120, 120, 120, 500, 300};

uint64_t nowUs() { return (uint64_t)esp_timer_get_time(); }

// Media di 32 letture distribuite nel tempo: nessun delay aggiuntivo.
void updateBattery() {
  uint32_t ms = millis();
  if (!BATTERY_MONITOR_ENABLED) {
    if (ms - batteryLastMs < 1000) return;
    batteryLastMs = ms;
    if (greeted && client.connected())
      client.println("{\"type\":\"battery\",\"enabled\":false,\"volts\":null}");
    return;
  }
  if (ms - batteryLastMs < 32) return;
  batteryLastMs = ms;
  batterySumMv += analogReadMilliVolts(BATTERY_PIN);
  if (++batteryCount < 32) return;
  float mv = batterySumMv / 32.0f;
  float volts = mv * 0.001f * (BATTERY_R_TOP + BATTERY_R_BOTTOM) / BATTERY_R_BOTTOM * BATTERY_CAL_FACTOR;
  batterySumMv = 0; batteryCount = 0;
  // Una misura non plausibile non va presentata come batteria carica o scarica.
  bool valid = mv >= 150 && mv <= 2800 && volts >= 4.0f && volts <= 8.6f;
  if (greeted && client.connected()) {
    client.printf("{\"type\":\"battery\",\"enabled\":true,\"valid\":%s,\"volts\":%.3f,\"t_us\":%llu,\"session\":\"%s\"}\n",
      valid ? "true" : "false", volts, (unsigned long long)nowUs(), sessionId.c_str());
  }
}

// Lettura controllata: non si riutilizzano valori vecchi se il bus I2C fallisce.
bool readRaw(float *v) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(IMU_ADDR, (uint8_t)14, (uint8_t)true) != 14) return false;
  int16_t raw[7];
  for (int i = 0; i < 7; i++) {
    uint16_t hi = Wire.read();
    raw[i] = (int16_t)((hi << 8) | Wire.read());
  }
  for (int i = 0; i < 3; i++) v[i] = raw[i] / 16384.0f;
  for (int i = 0; i < 3; i++) v[i + 3] = raw[i + 4] / 65.5f;
  return true;
}

void event(const char *name, uint64_t t = 0) {
  if (!t) t = nowUs();
  if (greeted && client.connected())
    client.printf("{\"type\":\"event\",\"name\":\"%s\",\"session\":\"%s\",\"t_us\":%llu,\"led\":%d}\n",
                  name, sessionId.c_str(), (unsigned long long)t, ledState ? 1 : 0);
}

void status() {
  if (client.connected())
    client.printf("{\"type\":\"status\",\"protocol\":1,\"boot\":\"%s\",\"ready\":%s,\"recording\":%s,\"error\":\"%s\"}\n",
                  bootId.c_str(), ready ? "true" : "false", recording ? "true" : "false", imuError.c_str());
}

bool calibrationFailed(const char *reason) {
  imuError = reason;
  Serial.print("CAL FALLITA: "); Serial.println(reason);
  return false;
}

bool calibrate() {
  ready = false;
  filtered = false;
  digitalWrite(WARNING_LED, HIGH);
  Serial.println("Calibrazione v1.1: appoggiare su supporto stabile e non toccare.");
  Serial.println("Attesa assestamento; non e' necessario azzerare l'inclinazione.");
  imu.initialize();
  if (!imu.testConnection()) return calibrationFailed("IMU_NOT_FOUND");
  imu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
  imu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
  delay(1000);
  // Welford: media e varianza senza sottrarre numeri quasi uguali.
  double mean[6] = {}, m2[6] = {};
  constexpr int N = 400;
  for (int n = 0; n < N; n++) {
    float v[6];
    if (!readRaw(v)) return calibrationFailed("I2C_READ_FAILED");
    for (int j = 0; j < 6; j++) {
      double delta = v[j] - mean[j];
      mean[j] += delta / (n + 1);
      m2[j] += delta * (v[j] - mean[j]);
    }
    delay(5);
  }
  const char *names[] = {"AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"};
  bool moving = false, gyroBias = false;
  for (int j = 0; j < 6; j++) {
    double sd = sqrt(m2[j] / (N - 1));
    double limit = j < 3 ? 0.025 : 0.8;
    Serial.printf("CAL %s media=%.5f std=%.5f limite_std=%.3f %s\n",
      names[j], mean[j], sd, limit, sd > limit ? "INSTABILE" : "OK");
    if (sd > limit) moving = true;
    if (j >= 3 && fabs(mean[j]) > 5.0) gyroBias = true;
  }
  double norm = sqrt(mean[0]*mean[0] + mean[1]*mean[1] + mean[2]*mean[2]);
  Serial.printf("CAL norma_acc=%.5f g (attesa 0.75..1.25)\n", norm);
  if (moving) return calibrationFailed("CAL_MOVING");
  if (gyroBias) return calibrationFailed("CAL_GYRO_BIAS");
  if (norm < 0.75 || norm > 1.25) return calibrationFailed("CAL_ACCEL_NORM");
  // Una sola posa non distingue inclinazione e offset accelerometrico.
  // Conservare la gravita' misurata: calibrare qui soltanto il bias gyro.
  for (int j = 0; j < 3; j++) bias[j] = 0;
  for (int j = 3; j < 6; j++) bias[j] = mean[j];
  imuError = "";
  ready = true;
  digitalWrite(WARNING_LED, LOW);
  lastSample = 0;
  nextSample = nowUs();
  Serial.println("CAL OK: giroscopio calibrato, accelerometro non azzerato.");
  return true;
}

void beginSync(const char *label) {
  connectBlink = 0;
  syncLabel = label;
  syncStep = 0;
  ledState = true;
  digitalWrite(WARNING_LED, HIGH);
  uint64_t t = nowUs(); // Tempo della scrittura GPIO, prima dell'invio di rete.
  syncDeadline = t + SYNC_MS[0] * 1000ULL;
  event((syncLabel + "_LED_ON").c_str(), t);
}

void updateLed() {
  uint64_t t = nowUs();
  if (syncStep >= 0) {
    if (t < syncDeadline) return;
    syncStep++;
    if (syncStep >= 6) {
      syncStep = -1;
      event((syncLabel + "_SYNC_DONE").c_str());
      if (stopping) {
        event("STOP"); recording = false; stopping = false; sessionId = "";
      }
    } else {
      ledState = (syncStep % 2 == 0);
      digitalWrite(WARNING_LED, ledState);
      t = nowUs();
      syncDeadline = t + SYNC_MS[syncStep] * 1000ULL;
      event((syncLabel + (ledState ? "_LED_ON" : "_LED_OFF")).c_str(), t);
      return;
    }
  }
  uint32_t ms = millis();
  if (!wifiOk || !ready) {
    // Due impulsi = rete, tre = IMU. Pausa fino a completare 2 secondi.
    int count = !wifiOk ? 2 : 3;
    uint32_t phase = ms % 2000;
    ledState = phase < (uint32_t)count * 240 && phase % 240 < 120;
  } else if (connectBlink && ms - connectBlink < 1600) {
    ledState = (ms - connectBlink) % 800 < 500;
  } else {
    connectBlink = 0;
    ledState = false; // Fuori dai pattern rimane spento: ogni flash video e' distinguibile.
  }
  digitalWrite(WARNING_LED, ledState);
}

void reject(const char *reason) {
  if (client.connected()) client.printf("{\"type\":\"error\",\"error\":\"%s\"}\n", reason);
}

void handleCommand(String cmd) {
  cmd.trim();
  lastPing = millis();
  if (cmd == "HELLO") { greeted = true; connectBlink = millis(); status(); }
  else if (!greeted) reject("HELLO_REQUIRED");
  else if (cmd == "PING") status();
  else if (cmd == "CAL") {
    if (recording) { reject("RECORDING"); return; }
    calibrate(); lastPing = millis(); status(); event("CALIBRATION_DONE");
  } else if (cmd.startsWith("START ")) {
    String id = cmd.substring(6);
    bool valid = id.length() > 0 && id.length() <= 64;
    for (unsigned int i = 0; i < id.length(); i++)
      if (!isalnum((unsigned char)id[i]) && id[i] != '_' && id[i] != '-') valid = false;
    if (!ready || recording || !valid) { reject("START_REJECTED"); return; }
    sessionId = id; recording = true; stopping = false;
    event("START"); beginSync("START");
  } else if (cmd == "STOP") {
    if (!recording || stopping || syncStep >= 0) { reject("SYNC_BUSY_OR_IDLE"); return; }
    stopping = true; beginSync("STOP");
  } else if (cmd == "MARK") {
    if (!recording || syncStep >= 0 || stopping) { reject("SYNC_BUSY_OR_IDLE"); return; }
    event("MARK"); beginSync("MARK");
  } else reject("UNKNOWN_COMMAND");
}

void setup() {
  Serial.begin(115200);
  pinMode(WARNING_LED, OUTPUT); pinMode(BOARD_LED, OUTPUT);
  digitalWrite(WARNING_LED, LOW);
  char boot[24]; snprintf(boot, sizeof(boot), "%08lx%08lx", (unsigned long)esp_random(), (unsigned long)esp_random());
  bootId = boot;
  if (BATTERY_MONITOR_ENABLED) {
    pinMode(BATTERY_PIN, INPUT);
    analogReadResolution(12);
    analogSetPinAttenuation(BATTERY_PIN, ADC_11db);
  }
  Wire.begin(); // Pin predefiniti della stessa board usata nello sketch verificato.
  Wire.setClock(400000); // Entro la specifica MPU6050; sufficiente a 100 Hz.
  Wire.setTimeOut(20);
  WiFi.mode(WIFI_AP);
  wifiOk = WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
  if (wifiOk) wifiOk = WiFi.softAP(SSID, PASSWORD, 1, 0, 1);
  if (wifiOk) { server.begin(); Serial.println("WiFi FoilScoot-IMU, IP 192.168.4.1, TCP 8765"); }
  else Serial.println("ERRORE CREAZIONE RETE: riavviare la scheda.");
  delay(3000);
  calibrate();
  Serial.println(ready ? "IMU pronta" : imuError);
}

void loop() {
  if (wifiOk && !client.connected()) {
    if (greeted) {
      recording = false; stopping = false; syncStep = -1; sessionId = "";
      greeted = false; command = "";
    }
    client = server.available(); // Compatibile anche con Arduino-ESP32 2.x.
    if (client) { client.setNoDelay(true); lastPing = millis(); }
  }
  if (client.connected()) {
    if (millis() - lastPing > 8000) client.stop();
    int budget = 128;
    while (budget-- && client.available()) {
      char ch = client.read();
      if (ch == '\n') { handleCommand(command); command = ""; }
      else if (ch != '\r') {
        command += ch;
        if (command.length() > 96) { client.stop(); command = ""; break; }
      }
    }
  }
  updateLed();
  digitalWrite(BOARD_LED, millis() % 2000 < 80);
  uint64_t t = nowUs();
  if (ready && t >= nextSample) {
    uint64_t skipped = (t - nextSample) / SAMPLE_US;
    missed += skipped;
    nextSample += (skipped + 1) * SAMPLE_US;
    float raw[6];
    uint64_t sampleTime = nowUs(); // Inizio transazione I2C, non tempo di ricezione laptop.
    if (!readRaw(raw)) {
      ready = false; imuError = "I2C_READ_FAILED";
      event("IMU_ERROR"); recording = false; stopping = false; syncStep = -1;
      status(); sessionId = "";
    } else {
      float dt = lastSample ? (sampleTime - lastSample) / 1000000.0f : 0.01f;
      lastSample = sampleTime;
      // Costanti di tempo equivalenti ai filtri originali a 2 kHz.
      for (int j = 0; j < 6; j++) {
        float alpha = 1.0f - expf(-dt / (j < 3 ? 0.003315f : 0.004746f));
        float corrected = raw[j] - bias[j];
        values[j] = filtered ? values[j] + alpha * (corrected - values[j]) : corrected;
      }
      filtered = true;
      sequence++;
      if (greeted && client.connected())
        client.printf("{\"type\":\"data\",\"session\":\"%s\",\"seq\":%llu,\"t_us\":%llu,\"missed\":%llu,\"v\":[%.5f,%.5f,%.5f,%.5f,%.5f,%.5f]}\n",
          sessionId.c_str(), (unsigned long long)sequence, (unsigned long long)sampleTime, (unsigned long long)missed,
          values[0], values[1], values[2], values[3], values[4], values[5]);
    }
  }
  updateBattery();
  delay(1); // Lascia tempo a WiFi e watchdog; campionamento nominale, non hard real-time.
}
