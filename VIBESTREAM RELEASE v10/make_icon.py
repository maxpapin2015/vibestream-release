from PIL import Image, ImageDraw

def create_ico(path="vibestream.ico"):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark circular background + Spotify green inner circle
    draw.ellipse((8, 8, size - 8, size - 8), fill=(18, 18, 18, 255), outline=(29, 185, 84, 255), width=10)
    draw.ellipse((34, 34, size - 34, size - 34), fill=(29, 185, 84, 255))

    # Three sleek curved sound wave bars in black
    draw.arc((64, 78, 192, 178), start=205, end=335, fill=(12, 12, 12, 255), width=16)
    draw.arc((78, 106, 178, 186), start=205, end=335, fill=(12, 12, 12, 255), width=14)
    draw.arc((92, 134, 164, 194), start=205, end=335, fill=(12, 12, 12, 255), width=12)

    img.save(path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Generated", path)

if __name__ == "__main__":
    create_ico()
