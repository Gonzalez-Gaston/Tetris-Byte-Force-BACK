from fastapi import APIRouter, UploadFile, File, HTTPException
from src.models.cloudinary_model import CloudinaryModel

router = APIRouter()

cloudinary_model = CloudinaryModel()

@router.post("/upload_image/")
async def upload_image(image: UploadFile = File(...), folder: str = "default_folder", public_id: str = "default_id"):
    try:
        result = cloudinary_model.upload_image(image, folder, public_id)
        return {"message": "Image uploaded successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transform_image/")
async def transform_image(public_id: str, width: int, height: int):
    try:
        transformed_url = cloudinary_model.transform_image(public_id, width, height)
        return {"message": "Image transformed successfully", "url": transformed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_image/")
async def delete_image(public_id: str):
    try:
        result = cloudinary_model.delete_image(public_id)
        return {"message": "Image deleted successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
