from django.db import models
class EncryptedImage(models.Model):
    doctor_name = models.CharField(max_length=100)
    s_box = models.JSONField()  # To store the S-box
    json_data = models.JSONField()  # To store the JSON data
    encrypted_image_path = models.CharField(max_length=250)  # To store the path of the encrypted image
    uploaded_image = models.ImageField(upload_to='uploaded_images/', default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encrypted Image by {self.doctor_name} at {self.created_at}"
