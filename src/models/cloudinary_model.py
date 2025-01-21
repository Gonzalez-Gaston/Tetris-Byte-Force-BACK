import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from decouple import config
from fastapi import UploadFile

class CloudinaryModel:
    def __init__(self):
        cloudinary.config( 
            cloud_name = config('CLOUD_NAME'),
            api_key = config('API_KEY'), 
            api_secret = config('API_SECRET'), 
            secure=True
        )

    def upload_image(self, image: UploadFile, folder: str, public_id: str):
        result = cloudinary.uploader.upload(image.file, folder=folder, public_id=public_id, overwrite=True)
        return result

    def transform_image(self, public_id: str, width: int, height: int):
        transformed_url, _ = cloudinary_url(public_id, width=width, height=height, crop="scale")
        return transformed_url

    def delete_image(self, public_id: str):
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        return result


