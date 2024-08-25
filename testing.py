from ultralytics import YOLO
import cv2
import os
from PIL import Image

# Load the YOLOv8 model (you can change the model to 'yolov8s.pt', 'yolov8m.pt', etc.)
model_path = r'X:\Skripsi\trained datasets\train12\weights\best.pt'
model = YOLO(model_path)  # YOLOv8 nano version

# List of image paths (replace with your actual image paths)
image_paths = [
    r'C:\Users\Lenovo\Downloads\uji\cibadak.png',
    r'C:\Users\Lenovo\Downloads\uji\pasteur.png',
    r'C:\Users\Lenovo\Downloads\uji\sukajadi.png',
    r'C:\Users\Lenovo\Downloads\uji\gasibu.png', 
 
]

# Directory to save the output images
output_dir = 'output_images'
os.makedirs(output_dir, exist_ok=True)

# Perform inference on each image and save the result
for i, image_path in enumerate(image_paths):
    # Perform inference
    results = model(image_path)

    # Plot detections on the image
    annotated_image = results[0].plot()

    # Save the annotated image using PIL
    output_image_path = os.path.join(output_dir, f'output_image_{i+1}.png')
    annotated_image = Image.fromarray(annotated_image)
    annotated_image.save(output_image_path)
    
    print(f"Processed {image_path} - Saved result to {output_image_path}")

print("All PNG images have been processed and saved.")