from PIL import Image, ImageDraw

# Crear una imagen 256x256 con fondo transparente
img = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# Dibujar un círculo azul simple
draw.ellipse([50, 50, 206, 206], fill='blue')

# Guardar como ICO
img.save('app_icon.ico', format='ICO')
