
import fitz
doc = fitz.open()
page = doc.new_page()
rect = fitz.Rect(100, 100, 200, 200)

from PIL import Image
img = Image.new('RGB', (100, 100), color='red')
img.save('dummy.png')

page.insert_image(rect, filename='dummy.png')
print('Images after insert:', page.get_images())
xref = page.get_images()[0][0]

try:
    page.delete_image(xref)
    print('Deleted using page.delete_image')
except Exception as e:
    print('Error deleting:', e)
    print('dir(page):', [x for x in dir(page) if 'image' in x.lower() or 'del' in x.lower()])

