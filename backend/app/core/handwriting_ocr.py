import os
# [Fase 1] Windows PyTorch CPU Memory Bug Fix
# Membatasi pemecahan thread CPU ke 1 agar tidak memicu error `shm.dll` saat import Torch di Windows
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import cv2

class HandwritingOCR:
    def __init__(self):
        self.processor = None
        self.model = None
        self.is_loaded = False
        
    def load_model(self):
        if not self.is_loaded:
            print("Memuat model TrOCR untuk Tulisan Tangan... (Ini mungkin memakan waktu beberapa saat saat pertama kali)")
            try:
                from transformers import TrOCRProcessor, VisionEncoderDecoderModel
                import torch
                
                model_name = "microsoft/trocr-base-handwritten"
                self.processor = TrOCRProcessor.from_pretrained(model_name)
                self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
                self.is_loaded = True
                print("TrOCR berhasil dimuat!")
            except Exception as e:
                print(f"[ERROR] Gagal memuat TrOCR: {e}")
                self.is_loaded = False

    def recognize_text(self, image: np.ndarray) -> str:
        """
        Mengenali teks dari potongan gambar (crop) menggunakan TrOCR.
        """
        self.load_model()
        if not self.is_loaded:
            return ""
            
        import torch
        from PIL import Image
        
        # TrOCR mengharapkan gambar RGB dalam format PIL
        if len(image.shape) == 2: # Jika grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4: # Jika RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else: # BGR to RGB (standar OpenCV)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        pil_image = Image.fromarray(image).convert("RGB")
        
        # Proses gambar menjadi pixel values
        pixel_values = self.processor(pil_image, return_tensors="pt").pixel_values
        
        # Generate teks
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)
            
        # Decode hasil
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return generated_text.strip()

# Singleton instance
handwriting_engine = HandwritingOCR()
