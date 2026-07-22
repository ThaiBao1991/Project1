
import fitz
import numpy as np
from PIL import Image

doc = fitz.open()
page = doc.new_page()
rect = fitz.Rect(100, 100, 200, 200)

img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
img.save('dummy.png')

page.insert_image(rect, filename='dummy.png')
xref = page.get_images()[0][0]

pix = fitz.Pixmap(doc, xref)
print('Pixmap colorspace:', pix.colorspace)
print('Pixmap alpha:', pix.alpha)
print('Pixmap size:', pix.width, pix.height)

# Convert to PIL
img_extracted = Image.frombytes('RGB' if pix.alpha == 0 else 'RGBA', (pix.width, pix.height), pix.samples)
print('Equal?', np.array_equal(np.array(img), np.array(img_extracted)))


