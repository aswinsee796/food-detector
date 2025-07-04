from pyzbar.pyzbar import decode
from PIL import Image

img = Image.open("/Users/aswinsee796gmail.com/Downloads/barcode.jpg").convert("L")
result = decode(img)

for obj in result:
    print("✅ Type:", obj.type)
    print("✅ Data:", obj.data.decode("utf-8"))

if not result:
    print("⚠️ No barcode detected")
