# Football-Player-Tracker

This project is an AI-powered football game analyzer that uses object detection to identify and track key elements on the pitch — including players, referees, and the ball. It aims to provide automated insights into game dynamics through computer vision.

## How it was made

**Tech used:**

- Python – The core programming language for scripting, model integration, and data processing.
- YOLOv11 – The object detection model used to identify players, the ball, referees, and other key elements in each frame.
- NumPy – For efficient numerical and array operations.
- Matplotlib – Used for visualizing detections and debugging frame-by-frame analysis.

The AI model was trained on this [ data set ](https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc/dataset/1), using Google Colab to leverage free GPU resources for faster training.

Afterwards, the model was integrated into a Python-based tracker that processes video footage frame by frame. Bounding boxes are drawn around detected elements, and basic logic is implemented to attempt identification and tracking over time.

## How it Looks

![Image](https://i.imgur.com/Mh31A5S.png)

## Known Issues

- Goalkeeper Detection: Goalkeepers often wear colors different from their team, which breaks color-based team classification — currently, their IDs are hardcoded.
- Crowded Areas: The model struggles with tracking accuracy when too many players are clustered together.
- Ball Misidentification: If the ball is not visible, the tracker defaults to a common penalty spot location, which may lead to incorrect assumptions.

## Lesseons Learned

This was not only my first Computer Vision project, but also my first meaningful deep learning application. Throughout the process, I gained valuable experience in:

- Understanding how object detection models like YOLO work under the hood.
- Training custom AI models using annotated datasets and tuning them for real-world performance.
- Using Google Colab for large-scale training with limited hardware resources.
- Building logic to convert raw model outputs into something structured and usable — like a player tracking system.
- Dealing with the limitations and edge cases of AI in real-world scenarios (e.g., visual occlusion, similarity between players, lighting issues).

This project sparked a deeper interest in AI, especially its applications in sports analytics and real-time tracking systems.
