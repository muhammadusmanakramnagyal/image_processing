from django.shortcuts import render
from django.http import JsonResponse
from encrpyt.models import EncryptedImage
from PIL import Image
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from django.conf import settings

def encrypted_image_list(request):
    encrypted_images = EncryptedImage.objects.all()  # Query all EncryptedImage objects
    return render(request, 'db_and_decrypt.html', {'encrypted_images': encrypted_images})

class CustomAES:
    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def _sub_bytes(self, state, sbox):
        return bytes([sbox[b] for b in state])

    def decrypt(self, ciphertext, sbox, inverse_sbox):
        blocks = [ciphertext[i:i + AES.block_size] for i in range(0, len(ciphertext), AES.block_size)]
        plaintext = b''

        for block in blocks:
            state = self.cipher.decrypt(block)
            plaintext += self._sub_bytes(state, inverse_sbox)

        return unpad(plaintext, AES.block_size)

def decrypt_image(request):
    if request.method == 'POST':
        image_id = request.POST.get('image_id')
        if not image_id:
            return JsonResponse({'error': 'Image ID is required.'})

        try:
            encrypted_image_record = EncryptedImage.objects.get(id=image_id)
        except EncryptedImage.DoesNotExist:
            return JsonResponse({'error': 'Encrypted image not found.'})

        s_box = encrypted_image_record.s_box
        if isinstance(s_box, str):
            s_box = json.loads(s_box)

        json_data = json.loads(encrypted_image_record.json_data)
        encrypted_image_path = encrypted_image_record.encrypted_image_path

        inverse_s_box = [0] * 256
        for i in range(256):
            inverse_s_box[s_box[i]] = i

        try:
            # Load the encrypted image
            encrypted_image = Image.open(encrypted_image_path)
        except Exception as e:
            return JsonResponse({'error': f"An error occurred while opening the encrypted image: {e}"})

        aes_key = b'This is a key123'  # Ensure this key matches the encryption key
        custom_aes = CustomAES(aes_key)
        block_size = 16

        try:
            for block_info in json_data["blocks"]:
                x, y = block_info["x"], block_info["y"]
                encrypted_block = bytes.fromhex(block_info["encrypted_block"])
                decrypted_block_bytes = custom_aes.decrypt(encrypted_block, s_box, inverse_s_box)

                try:
                    decrypted_block = Image.frombytes('RGB', (block_size, block_size), decrypted_block_bytes)
                    encrypted_image.paste(decrypted_block, (x, y))
                except Exception as e:
                    # Handle image-related errors
                    print(f"Image error: {e}")

            # Save the decrypted image
            decrypted_folder = os.path.join(settings.MEDIA_ROOT, 'decrypted')
            os.makedirs(decrypted_folder, exist_ok=True)
            decrypted_image_path = os.path.join(decrypted_folder, os.path.basename(encrypted_image_path))

            encrypted_image.save(decrypted_image_path)

            # Construct the media-relative path to return in the response
            decrypted_image_url = os.path.join(settings.MEDIA_URL, 'decrypted', os.path.basename(encrypted_image_path))

            return JsonResponse({'success': True, 'decrypted_image_path': decrypted_image_url})
        except Exception as e:
            return JsonResponse({'error': f"An error occurred during decryption: {e}"})
