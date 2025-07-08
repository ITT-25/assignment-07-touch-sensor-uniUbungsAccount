## 🖼️ Dokumentation über den Aufbau, Design-Entscheidungen und Anwendungshinweise zum Touch Input

| Bild | Beschreibung |
| :--- | :----------- |
| ![Fertiger Touch-Sensor Box](TouchSensor1.png) | Außengehäuse: Quadratische Pappschachtel mit Dimensionen 28x28x33cm mit Acryl-Deckfläche und dickem Papier als Diffusor. Die Ecken wurden nach oben geklappt und mit Tesa verstärk, um die Distanz zwischen Kamera und Touch-Fläche zu erhöhen. |
| ![Innenleben](TouchSensor2.png) | Innenansicht: Eigene USB-Webcam (ersetzt ursprünglich geplante Intel RealSense-Kamera da diese nicht funktionierte). Die Kamera benötigt einen USB 2.0-Anschluss und bietet 60FPS 1080P Video. Das Kabel wird durch ein loch aus der Unterseite der Box geführt. |

# Design-Entscheidungen für Touch Erkennung


Für bessere Wahrnehmung des Fingers werden verschiedene Tricks benutzt:
-   Zunächst kalibiert der Touch Input sich beim Programmstart für 3s selbst, um sich an die Lichtverhältnisse anzupassen. 
-   Das Bild von der Kamera um 10% zugeschnitten, um etwaige Ränder der Box zu entfernen.
-   Es wird zwischen frames gesmoothed um flickern zu bekämpfen
-   Um Taps zu erkennen wird nach kurzen Erkennungen bis 0.35s gesucht, funktioniert zuverlässig
-   Um zu kleine oder große Flächen nicht zu erkennen, werden minimum und maximum Kontourgrößen definiert

Zum Testen kann fitts_law.py benutzt werden. Es klappt zuverlässig, mit dem Touch-Input die roten Kreise anzuklicken, allerdings ist ist es relativ langsam verglichen mit einer Maus, wie man der .csv Datei danach entnehmen kann.

# Design-Entscheidungen für die Buchstaben-Erkennung
Um die Handgeschriebenen Buchstaben zu erkennen wurde der 1$-Recognizer-Ansatz gewählt, da er simpel ohne und großes Datenset implementierbar ist und sehr gute Ergebnisse erzielen kann. Zudem ist er schnell und effizient, was z. B. dem Touch-Input Device erlauben könnte, mit einem Raspberry Pie als tragbares stand-alone-Gerät zu existieren.

Der 1$ Recognizer wurde auf Threshhold 75% accuracy gesetzt um unklare Inputs zu filtern, und erlaubt damit meist zuverlässiges schreiben. Zustätzlich wäre es sehr schnell möglich, die 26 Buchstaben des Alphabets durch weitere Symbole zu erweitern, oder es Nutzern zu erlauben, selbst Buchstaben-Shapes zu definieren, so wie sie schreiben wollen. Auch kleingeschriebene Buchstaben könnten unterstützt werden. Damit Nutzer die erwartete Zeichen-Form sehen können, poppt beim Programmstart ein 2. Fenster mit Guide auf. Dieses ist adaptiv und passt sich an die Menge der .xml-Shape-Dateien im Ordner an.

# Anwendungshinweise

Gute Lichtverhältnisse sind vorteilhaft aber nicht zwingend nötig, da der Touch Input sich selbst kalibiert. Man kann mit dem Finger steuern, allerdings kann der Schatten der Hand etwas stören, weswegen schwarze lange Objekte als Touch-Device in der Regel besser funktionieren. 

Um die 2 Touch-Programme zu beenden kann `esc` gedrückt werden.

# Fazit

Der Touch-Input fühlt sich irgendwie magisch an und ist eine low-cost solution mit coolem Potential. Für die meisten Anwendungszwecke dürfte allerdings ein klassischer Touchscreen sinnvoller sein.
