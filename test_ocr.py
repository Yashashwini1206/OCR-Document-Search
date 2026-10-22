
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

image_path = input("Enter the full image path: ").strip().strip('"')

try:
    image = Image.open(image_path).convert("RGB")
    print("Image loaded successfully")
    print("Original image size:", image.size)

    # Enlarge and improve contrast for handwriting
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(2)
    image = image.resize((image.width * 2, image.height * 2))
    image = image.filter(ImageFilter.SHARPEN)

    print("\nRecognized text:\n")

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 11"
    )
    print(text if text.strip() else "No text recognized.")

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config="--psm 6",
        output_type=pytesseract.Output.DICT
    )

    words = [
        word for word in data["text"]
        if word.strip()
    ]

    print("\nTotal detected words:", len(words))

except Exception as error:
    print("Error:", error)
print("\nChecking for the word 'objects':")

recognized_text = text.casefold()

if "objects" in recognized_text:
    print("Found 'objects' in OCR text.")
else:
    print("'objects' was NOT recognized exactly.")