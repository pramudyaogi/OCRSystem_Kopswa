import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_use_onednn"] = "0"

import numpy as np
import cv2
import traceback
from app.core.ocr.ocr_engine import extract_text_from_crop

print("Testing direct OCR with MKLDNN disabled...")
dummy_img = np.zeros((800, 600, 3), dtype=np.uint8)

try:
    print("Calling extract_text_from_crop...")
    res = extract_text_from_crop(dummy_img)
    print("Success!", res)
except Exception as e:
    print("ERROR CAUGHT:")
    traceback.print_exc()
