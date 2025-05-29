from PIL import Image
import numpy as np

def apply_customization(qr_image, color_hex="#000000", size_pixels=0): # (PIL image, hex code, size of qr)
    # converting hex color to RGB
    color_hex = color_hex.lstrip('#')
    rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    
    # converting image to numpy array 
    img_array = np.array(qr_image)
    
    # create black mask for the black parts
    black_mask = (img_array[..., 0] == 0) & (img_array[..., 1] == 0) & (img_array[..., 2] == 0)
    
    # changing color to rgb one
    img_array[black_mask] = rgb
    
    # converting into image
    customized_img = Image.fromarray(img_array)
    
    # resize if requested
    if size_pixels > 0:
        customized_img = customized_img.resize((size_pixels, size_pixels), Image.NEAREST)
    
    return customized_img