import cv2
from pyzxing import BarCodeReader
import csv



reader = BarCodeReader()
results = reader.decode("tets.jpg")
print(results)



