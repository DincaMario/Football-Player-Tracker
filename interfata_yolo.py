from ultralytics import YOLO

model = YOLO('modele/best.pt')

result = model.predict('Clip_test/08fd33_4.mp4', save=True)

print(result[0])
print("==============================")
for box in result[0].boxes:
    print(box)
