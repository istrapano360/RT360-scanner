//test program -- radi! ovaj je zadnji
#include <Stepper.h>

const int stepsForFullTurn = 6144;
const int stepsPerRevolution = 2048;
const int stepsFor90Degrees = 1536;
const int stepsFor45Degrees = 768;
const int stepsFor30Degrees = 512;
const int stepsFor5Degrees = 96;

const int stepInterval = 2; // milisekundi između koraka
const int startButtonPin = 6;
const int stopButtonPin = 7;
const int programButtonPin = 8;
const int RED_PIN = 14;
const int GREEN_PIN = 15;
const int BLUE_PIN = 16;

bool isRunning = false;
bool programButtonPressed = false; 
bool waitingForPi = false;
bool singleShotEntryLock = false;
bool singleShotMode = false;

unsigned long lastStepTime = 0;
unsigned long piWaitStartTime = 0;
unsigned long singleShotHoldStart = 0;

int program = 6;
int stepsTaken = 0; // Brojač koraka
int turn = 0;


Stepper myStepper(stepsPerRevolution, 2, 4, 3, 5); // IN1=D2, IN2=D3, IN3=D4, IN4=D5

bool checkPiReady() {
  Serial.println("RDY?");
  piWaitStartTime = millis();
  waitingForPi = true;
  
  while(waitingForPi) {
    if(Serial.available()) {
      String response = Serial.readStringUntil('\n');
      if(response == "READY") {
        waitingForPi = false;
        return true;
      }
    }
        // Omogući korisniku da prekine čekanje s STOP tipkom:
    if (digitalRead(stopButtonPin) == LOW) {
        Serial.println("Prekid čekanja Pi READY (STOP pritisnut)");
        waitingForPi = false;
        return false;
    }

    if(millis() - piWaitStartTime > 15000) {
      waitingForPi = false;
      return false;
    }
    delay(10);
  }
  return false;
}

void trigger() {
  delay(1800);
}

void setLEDColor(int red, int green, int blue) {
  analogWrite(RED_PIN, red);    // Postavi crvenu boju
  analogWrite(GREEN_PIN, green); // Postavi zelenu boju
  analogWrite(BLUE_PIN, blue);   // Postavi plavu boju
}

// Dodajte ove funkcije negdje u kodu (van switch-case):
void handleError() {
    isRunning = false;
    settpinoff();
    for(int i = 0; i < 10; i++) {
        setLEDColor(255, 0, 0);
        delay(150);
        setLEDColor(0, 0, 0);
        delay(150);
    }
    setProgramLED();
    Serial.println("Greska: Problem s komunikacijom s Raspberry Pi!");
}

void setProgramLED() {
  switch(program) {
    case 1: setLEDColor(0, 255, 0); break;   // Purple for program 1
    case 2: setLEDColor(255, 0, 0); break;   // Cyan for program 2
    case 3: setLEDColor(0, 0, 255); break;   // Yellow for program 3
    case 4: setLEDColor(255, 0, 255); break;   // Green for program 4
    case 5: setLEDColor(0, 255, 255); break;   // Red for program 5
    case 6: setLEDColor(255, 55, 100); break;   // Aquamarine? for program 6
    //case 7: setLEDColor(255, 255, 0); break;   // Blue for program 6
  }
}

void programdone() {
  for(int i = 0; i < 4; i++) {
          setLEDColor(0, 0, 0);
          delay(150);
          setLEDColor(255, 255, 255);
          delay(150);
      }
}
void changeProgram() {
  // Provjeri je li tipka pritisnuta i da nismo već reagirali na ovaj pritisak
  if (digitalRead(programButtonPin) == LOW && !programButtonPressed) {
    programButtonPressed = true;  // Označi da smo reagirali na pritisak
    program++;
    if (program > 6) {
      programdone();  
      program = 1;
    }
    setProgramLED();  // Postavi odgovarajuću boju LED
    Serial.print("Odabran program: ");
    Serial.println(program);
    delay(300);  // Debounce delay
  }
  else if (digitalRead(programButtonPin) == HIGH) {
    programButtonPressed = false;  // Resetiraj stanje kada je tipka otpuštena
  }
}

void settpinoff() {
    digitalWrite(2, LOW);
    digitalWrite(3, LOW);
    digitalWrite(4, LOW);
    digitalWrite(5, LOW);
  }

bool handleStepAndTrigger(int stepsNeeded, int turnsNeeded) {
    if (turn == 0) {
        trigger();
        turn++;
    } else if (stepsTaken < stepsNeeded) {
        if (millis() - lastStepTime >= stepInterval) {
            myStepper.step(1);
            stepsTaken++;
            lastStepTime = millis();
        }
    } else if (turn < turnsNeeded) {
        turn++;
        isRunning = false;
        settpinoff();
        trigger();
        stepsTaken = 0;
        delay(300);
        isRunning = true;
    } else {
        settpinoff();
        isRunning = false;
        turn = 0;
        programdone();
        setProgramLED();
        Serial.println("Program " + String(program) + " završen");
        return true; // završen program
    }
    return false; // još traje
}

void setup() {
  Serial.begin(115200);
  unsigned long serialWaitStart = millis();
  while (!Serial && millis() - serialWaitStart < 3000);
  delay(100);
  const char* messages[] = {
    "RT360 program za 3D rotacijski stol za skeniranje predmeta.",
    "Može se koristiti metoda fotogrametrije, scaner ili fotoaparat s triggerom (3.5mm audio jack), triger radi samo kontakt.",
    "Sadrži 6 programa označenih u bojama ledica.",
    "1. Jedan krug - Magenta",
    "2. Konstantna vrtnja - Cyan",
    "3. Periode od 90° - Yellow",
    "4. Periode od 45° - Green",
    "5. Periode od 30° - Red",
    "6. Periode od 5.6° - Blue",
    "Na kraju završenog programa ledica blinka, također i na nakon odabira zadnjeg programa",
    "Program 3, 4, 5 i 6 ujedno aktiviraju i trigger za fotoaparat.",
    "I ne, ne može se iz ovog arduina izvući C++ sketch ovog programa :)"
  };

  // Broj poruka u nizu
  int nmessages = sizeof(messages) / sizeof(messages[0]);

  // Ispis svih poruka s pauzom od 50ms
  for (int i = 0; i < nmessages; i++) {
    Serial.println(messages[i]);
    delay(50); // Pauza od 50ms nakon svakog reda
  }

  myStepper.setSpeed(10); // RPM 3-13
  pinMode(startButtonPin, INPUT_PULLUP);
  pinMode(stopButtonPin, INPUT_PULLUP);
  pinMode(programButtonPin, INPUT_PULLUP);
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  setProgramLED();
}

void loop() {
  // Handle STOP button (works anytime)
  static bool stopButtonPreviouslyPressed = false;
  static unsigned long stopLastPressed = 0;
  const unsigned long stopDebounceDelay = 300;

//Slušaj serijsku komunikaciju (uvijek)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "STEP") {
        Serial.println("ACK");
        for (int i = 0; i < 96; i++) {
            myStepper.step(1);
            delay(stepInterval);
        }
        settpinoff();
        Serial.println("DONE");
    }
  }

if (digitalRead(stopButtonPin) == LOW) {
  if (!stopButtonPreviouslyPressed && millis() - stopLastPressed > stopDebounceDelay) {
    stopButtonPreviouslyPressed = true;
    stopLastPressed = millis();

    isRunning = false;
    stepsTaken = 0;
    settpinoff();
    setProgramLED();
    Serial.println("STOP");
  }
} else {
  stopButtonPreviouslyPressed = false;
}

  // Handle PROGRAM button (only when stopped)
  if (!isRunning) {
    changeProgram();
  }

  // Handle START button (only when stopped)
  if (!isRunning && digitalRead(startButtonPin) == LOW) {
    isRunning = true;
    stepsTaken = 0;
    turn = 0;
    Serial.println("START");
    delay(300); // debounce
  }

  // Motor control logic
  if (isRunning) {
    switch (program) {
      case 1: // Full rotation
        if (stepsTaken < stepsForFullTurn) {
          if (millis() - lastStepTime >= stepInterval) {
            myStepper.step(1);
            stepsTaken++;
            lastStepTime = millis();
          }
        } else {
          isRunning = false;
          settpinoff();
          programdone();
          Serial.println("Puni okret završen");
          setProgramLED();
        }
        break;

      case 2: // Continuous rotation
        if (millis() - lastStepTime >= stepInterval) {
          myStepper.step(1);
          lastStepTime = millis();
        }
        break;

      case 3:
          handleStepAndTrigger(stepsFor90Degrees, 4);
          break;
      case 4:
          handleStepAndTrigger(stepsFor45Degrees, 8);
          break;
      case 5:
          handleStepAndTrigger(stepsFor30Degrees, 12);
          break;
      case 6:
          handleStepAndTrigger(stepsFor5Degrees, 65);
          break;
    }
  }
}