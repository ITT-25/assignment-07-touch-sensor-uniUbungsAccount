## David Ring (12/20P)

### Build a Camera-Based Touch Sensor (6P/10P)
* Hardware is assembled correctly
    * nothing is secured, no description for top/bottom (-1P)
* Bounding boxes around fingers are detected robustly, palm-rejection works
    * palm-rejection does not work, detection is not robust (-2P)
* Movement and taps can be distinguished and sent via DIPPID, making it compatible with the given Fitts’ Law application
    * tap recognition sometimes unreliable (-0.5P)
* Automatic calibration works
    * yep (1P)
* Documentation
    * yep (2P)
* cameraID is hardcoded (-0.5P)

### Touch-based Text Input (6/10P)
* Detection of finger or stylus works
    * nope (-1P)
* Input is captured and pre-processed reasonably
    * yep (2P)
* Reasonable approach for hand-writing recognition (-2P)
    * the mentioned customibility is not really achievable, because theres no application implemented and there could have been more xml files in different handwritings 
    * $1 recognizer might not be the best choice for this task 
* Robust detection
    * nopes (-0.5P)
* Acceptable latency
    * yep (1P)
* Mapping of handwriting to keyboard
    * only lower case recognized (-0.5P)
* Documentation
    * yep (2P)

