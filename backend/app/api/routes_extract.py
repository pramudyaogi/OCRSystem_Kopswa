import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.config import UPLOAD_DIR, BASE_DIR
from app.core.preprocessing import preprocess_pipeline
from app.core.template_matching import load_template_config, crop_fields_by_template
from app.core.ocr_engine import process_cropped_fields
from app.core.postprocessing import postprocess_extracted_data, convert_numpy_types

router = APIRouter()

@router.post("/{filename}")
@router.post("/{filename}/")
async def extract_document_data(filename: str, template_type: str = "ktp"):
    """
    Endpoint 'Jantung' Sistem. 
    Menggabungkan Preprocessing -> Crop -> OCR -> Validasi
    """
    try:
        image_path = UPLOAD_DIR / filename
        if not os.path.exists(image_path):
            return JSONResponse(status_code=404, content={"detail": f"File '{filename}' tidak ditemukan di storage server."})
            
        # 1. Load config template (Contoh: ktp_template.json)
        template_path = BASE_DIR / "app" / "templates_config" / f"{template_type}_template.json"
        if not os.path.exists(template_path):
            return JSONResponse(status_code=400, content={"detail": f"Template config untuk '{template_type}' tidak ditemukan."})
        
        template_config = load_template_config(str(template_path))
        
        # 2. Image Preprocessing (Deskew, Enhance, Safe Load)
        processed_img = preprocess_pipeline(str(image_path))
        if processed_img is None:
            return JSONResponse(status_code=400, content={"detail": "Gagal memproses gambar. Format file gambar tidak valid atau rusak."})
             
        # 3. Jalankan AI (PaddleOCR untuk KTP, TrOCR untuk Tulisan Tangan)
        from app.core.ocr_engine import extract_full_text
        from app.core.template_matching import extract_ktp_data_smart
        
        use_trocr = (template_type == "form_pendaftaran")
        full_text_blocks = extract_full_text(processed_img, use_trocr=use_trocr)
        print(f"\n================ [AI OCR RESULT] ================")
        for idx, b in enumerate(full_text_blocks):
            print(f"Blok {idx+1}: {b['text']} (Conf: {b['confidence']:.2f})")
        print(f"=================================================\n")
        
        # 4. Parsing cerdas menggunakan RegEx / pencocokan kata
        raw_extracted_data = extract_ktp_data_smart(full_text_blocks, template_config)
        print(f"\n================ [FINAL EXTRACTED DATA] ================")
        for k, v in raw_extracted_data.items():
            print(f"-> {k}: {v}")
        print(f"========================================================\n")
        
        # 5. Bersihkan dan validasi hasilnya
        final_data = postprocess_extracted_data(raw_extracted_data, template_config.get("fields", []))
        
        response_payload = {
            "status": "success",
            "template": template_type,
            "extracted_data": final_data
        }
        clean_payload = convert_numpy_types(response_payload)
        return JSONResponse(status_code=200, content=clean_payload)
    except HTTPException as http_exc:
        return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
    except Exception as e:
        import traceback
        err_msg = f"Gagal memproses OCR: {str(e)}"
        print(f"[OCR Error]: {err_msg}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": err_msg})
