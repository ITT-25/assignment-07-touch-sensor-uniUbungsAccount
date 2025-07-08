## 🖼️ Dokumentation über den Aufbau, Design-Entscheidungen und Anwendungshinweise zum Touch Input

| Bild | Beschreibung |
| :--- | :----------- |
| ![Fertige Touch-Sensor-Box](TouchSensor1.png) | Außengehäuse: Quadratische Pappschachtel mit den Dimensionen 28×28×33 cm, Acryl-Deckfläche und dickem Papier als Diffusor. Die Ecken wurden nach oben geklappt und mit Tesa verstärkt, um die Distanz zwischen Kamera und Touch-Fläche zu erhöhen. |
| ![Innenleben](TouchSensor2.png) | Innenansicht: Eigene USB-Webcam (ersetzt die ursprünglich geplante Intel RealSense-Kamera, da diese nicht funktionierte). Die Kamera benötigt einen USB-2.0-Anschluss und bietet ein 1080p-Video mit 60 FPS. Das Kabel wird durch ein Loch an der Unterseite der Box geführt. |

# Design-Entscheidungen für die Touch-Erkennung

Für eine bessere Wahrnehmung des Fingers werden verschiedene Tricks angewendet:

- Beim Programmstart kalibriert sich der Touch Input für 3 Sekunden selbst, um sich an die Lichtverhältnisse anzupassen.
- Das Bild der Kamera wird um 10 % zugeschnitten, um eventuelle Ränder der Box zu entfernen.
- Zwischen den Frames wird geglättet, um Flackern zu vermeiden.
- Um Taps zu erkennen, wird nach kurzen Berührungen bis maximal 0,35 s gesucht; dies funktioniert zuverlässig.
- Um zu kleine oder zu große Flächen nicht fälschlich zu erkennen, werden minimale und maximale Konturgrößen definiert.

Zum Testen kann `fitts_law.py` verwendet werden. Es funktioniert zuverlässig, die roten Kreise mit dem Touch-Input anzuklicken; allerdings ist dies im Vergleich zur Maus relativ langsam, wie man der erzeugten `.csv`-Datei entnehmen kann.

# Design-Entscheidungen für die Buchstaben-Erkennung

Um handgeschriebene Buchstaben zu erkennen, wurde der 1$-Recognizer-Ansatz gewählt, da er simpel ohne großes Datenset implementierbar ist und dennoch sehr gute Ergebnisse erzielen kann. Zudem ist er schnell und effizient, was es z. B. ermöglichen würde, das Touch-Input-Device als tragbares Standalone-Gerät mit einem Raspberry Pi zu betreiben.

Der 1$ Recognizer wurde auf einen Threshold von 75 % Genauigkeit gesetzt, um unklare Eingaben zu filtern, und ermöglicht damit meist zuverlässiges Schreiben. Zusätzlich wäre es einfach möglich, die 26 Buchstaben des Alphabets durch weitere Symbole zu erweitern oder Nutzern zu erlauben, eigene Buchstaben-Shapes zu definieren. Auch Kleinbuchstaben könnten unterstützt werden. Damit Nutzer die erwartete Zeichenform sehen können, öffnet sich beim Programmstart ein zweites Fenster mit einem Guide. Dieses ist adaptiv und passt sich an die Menge der `.xml`-Shape-Dateien im Ordner an.

# Anwendungshinweise

Gute Lichtverhältnisse sind vorteilhaft, aber nicht zwingend nötig, da sich der Touch Input selbst kalibriert. Man kann mit dem Finger steuern; allerdings könnte der Schatten der Hand etwas stören, weswegen längliche schwarze Objekte als Eingabegerät in der Regel besser funktionieren.

Die Kamera muss mittig in der Box sitzen. Die Ränder werden zwar programmatisch abgeschnitten, dennoch darf kein Rand der Box im Kamerabild sichtbar sein.

Um die beiden Touch-Programme zu beenden, kann die `Esc`-Taste gedrückt werden.

# Fazit

Der Touch Input fühlt sich irgendwie magisch an und ist eine low-cost Lösung mit coolem Potenzial. Für die meisten Anwendungszwecke dürfte allerdings ein klassischer Touchscreen sinnvoller sein.
