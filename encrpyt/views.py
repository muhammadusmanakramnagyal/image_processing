from django.shortcuts import render
import json
import os
from django.http import JsonResponse
from PIL import Image, UnidentifiedImageError
import numpy as np
from skimage.measure import shannon_entropy
from Crypto.Cipher import AES
from django.conf import settings
from Crypto.Util.Padding import pad, unpad
from .models import EncryptedImage
# Provided list of integers (Custom S-box)
custom_s_box = [194, 140, 158, 204, 202, 195, 162, 176, 121, 166, 55, 157, 45, 75, 61, 98, 92, 122, 215, 207, 102, 249, 134, 83, 168, 11, 42, 220, 41, 208, 169, 1, 67, 25, 127, 28, 184, 88, 190, 46, 197, 111, 0, 186, 156, 53, 173, 231, 223, 35, 33, 234, 109, 8, 101, 113, 97, 117, 91, 240, 54, 217, 68, 86, 206, 135, 52, 87, 95, 183, 103, 200, 205, 224, 112, 228, 115, 236, 12, 119, 255, 74, 182, 43, 253, 56, 34, 19, 118, 4, 39, 6, 36, 149, 171, 167, 84, 71, 243, 237, 132, 172, 2, 170, 116, 72, 108, 216, 93, 22, 23, 58, 254, 30, 179, 40, 241, 187, 155, 247, 78, 50, 177, 120, 24, 165, 178, 59, 20, 198, 16, 104, 244, 196, 191, 232, 13, 203, 214, 85, 81, 79, 174, 235, 238, 142, 139, 15, 160, 38, 213, 31, 90, 70, 21, 199, 138, 133, 129, 222, 209, 32, 7, 250, 161, 189, 246, 77, 73, 47, 146, 185, 230, 153, 137, 107, 233, 143, 5, 218, 100, 89, 201, 248, 159, 180, 136, 64, 29, 144, 239, 163, 251, 62, 94, 110, 152, 150, 226, 245, 148, 221, 18, 76, 123, 17, 125, 96, 9, 126, 63, 105, 225, 37, 69, 57, 114, 229, 27, 51, 44, 193, 82, 80, 154, 188, 124, 66, 164, 227, 147, 181, 3, 151, 192, 211, 219, 48, 145, 175, 252, 242, 99, 106, 60, 141, 212, 131, 65, 130, 26, 49, 210, 14, 128, 10]

# Generate the inverse S-box
inverse_s_box = [0] * 256
for i in range(256):
    inverse_s_box[custom_s_box[i]] = i

class CustomAES:
    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def _sub_bytes(self, state, sbox):
        return bytes([sbox[b] for b in state])

    def encrypt(self, plaintext):
        plaintext = pad(plaintext, AES.block_size)
        blocks = [plaintext[i:i + AES.block_size] for i in range(0, len(plaintext), AES.block_size)]
        ciphertext = b''

        for block in blocks:
            state = self._sub_bytes(block, custom_s_box)
            ciphertext += self.cipher.encrypt(state)

        return ciphertext

    def decrypt(self, ciphertext):
        blocks = [ciphertext[i:i + AES.block_size] for i in range(0, len(ciphertext), AES.block_size)]
        plaintext = b''

        for block in blocks:
            state = self.cipher.decrypt(block)
            plaintext += self._sub_bytes(state, inverse_s_box)

        return unpad(plaintext, AES.block_size)

def process_image(request):
    input_file = request.FILES.get('input_path')
    block_size = 16
    doctor_name = request.POST.get('doctor_name')
    aes_key = request.POST.get('aes_key')  # 16 bytes key

    # Create encrypted folder if it doesn't exist
    encrypted_folder = os.path.join(settings.MEDIA_ROOT, 'encrypted')
    os.makedirs(encrypted_folder, exist_ok=True)

    # Set the output path
    output_path = os.path.join(encrypted_folder, os.path.splitext(input_file.name)[0] + '_encrypted' + os.path.splitext(input_file.name)[1])
    try:
        binary_aes_key = aes_key.encode('utf-8')  # Converts the string to binary format (bytes)
    except Exception as e:
        return JsonResponse({'error': f"Invalid AES Key: {e}"})

    try:
        image = Image.open(input_file)
    except UnidentifiedImageError:
        return JsonResponse({'error': f"Cannot identify image file '{input_file.name}'."})
    except Exception as e:
        return JsonResponse({'error': f"An error occurred while opening the image: {e}"})

    custom_aes = CustomAES(binary_aes_key)

    try:
        width, height = image.size
        modified_blocks = []
        json_data = {
            "width": width,
            "height": height,
            "blocks": []
        }
        total_index = 0

        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                box = (x, y, min(x + block_size, width), min(y + block_size, height))
                block = image.crop(box)
                block_bytes = block.tobytes()
                gray_block = np.array(block.convert('L'))
                entropy = shannon_entropy(gray_block)

                if entropy > 3.0:
                    padding_length = block_size - len(block_bytes) % block_size
                    padded_block = block_bytes + bytes([padding_length] * padding_length)
                    encrypted_block = custom_aes.encrypt(padded_block)

                    modified_block = Image.frombytes(block.mode, block.size, encrypted_block)
                    modified_blocks.append(modified_block)

                    json_data["blocks"].append({
                        "index": total_index,
                        "x": x,
                        "y": y,
                        "encrypted_block": encrypted_block.hex()
                    })
                else:
                    modified_blocks.append(block)

                total_index += 1

        new_image = Image.new('RGB', (width, height))
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                block_index = (y // block_size) * (width // block_size) + (x // block_size)
                new_image.paste(modified_blocks[block_index], (x, y))

        # Save the new image
        new_image.save(output_path)

        # Create a URL for the encrypted image
        encrypted_image_url = os.path.join(settings.MEDIA_URL, 'encrypted', os.path.basename(output_path))

        # Save data in the database
        encrypted_image_record = EncryptedImage.objects.create(
            doctor_name=doctor_name,
            s_box=custom_s_box,
            json_data=json.dumps(json_data),
            encrypted_image_path=output_path,
            uploaded_image=input_file  # Save the uploaded image as well
        )

        return JsonResponse({'success': True, 'encrypted_image_url': encrypted_image_url})

    except Exception as e:
        return JsonResponse({'error': f"An error occurred during processing: {e}"})



from django.shortcuts import render

def image_encryption_form(request):
    return render(request, 'image_encryption_form.html')  # Update with your template name
