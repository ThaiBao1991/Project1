
import fitz
doc = fitz.open()
page = doc.new_page()
rect = fitz.Rect(100, 100, 200, 200)

# Create a dummy image
from PIL import Image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('dummy.png')

# Add stamp annotation
try:
    annot = page.add_stamp_annot(rect, stamp=0)
    
    # In newer PyMuPDF, we can set appearance stream to an image?
    # Let's try annot.set_appearance() or something?
    # PyMuPDF has a way to add image to an annotation?
    print(dir(annot))
except Exception as e:
    print('Error:', e)

