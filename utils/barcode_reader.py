import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image


def crop_to_barcode(image_path):
    """Detect and crop the region likely to contain a barcode"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Use gradient to emphasize barcode region
    grad_x = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    grad_y = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
    gradient = cv2.subtract(grad_x, grad_y)
    gradient = cv2.convertScaleAbs(gradient)

    # Blur and threshold
    blurred = cv2.blur(gradient, (9, 9))
    _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

    # Morphological operations to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    closed = cv2.erode(closed, None, iterations=2)
    closed = cv2.dilate(closed, None, iterations=2)

    # Find contours and sort by area
    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image_path  # fallback to original

    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    cropped = img[y:y + h, x:x + w]

    cropped_path = image_path.replace(".jpg", "_cropped.jpg")
    cv2.imwrite(cropped_path, cropped)
    return cropped_path


def read_barcode(image_path):
    """Crop image to barcode region and decode"""
    try:
        cropped_path = crop_to_barcode(image_path)
        image = Image.open(cropped_path).convert("L")  # Grayscale
        decoded_objects = decode(image)

        for obj in decoded_objects:
            if obj.type in ["EAN13", "EAN", "UPCA", "EAN8", "CODE128"]:
                return obj.data.decode("utf-8")
    except Exception as e:
        print("Barcode reading error:", e)

    return None
