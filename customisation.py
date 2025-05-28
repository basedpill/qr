from PIL import Image
import numpy as np

def apply_customization(qr_image, color_hex="#000000", size_pixels=0):
    """
    Apply customization to a QR code image
    :param qr_image: PIL Image object of the QR code
    :param color_hex: Hex color code for QR color (default: black)
    :param size_pixels: Output size in pixels (0 for default scaling)
    :return: Customized PIL Image
    """
    # Convert hex color to RGB
    color_hex = color_hex.lstrip('#')
    rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert image to numpy array for processing
    img_array = np.array(qr_image)
    
    # Create a mask for black pixels (QR code pattern)
    black_mask = (img_array[..., 0] == 0) & (img_array[..., 1] == 0) & (img_array[..., 2] == 0)
    
    # Apply custom color to black pixels
    img_array[black_mask] = rgb
    
    # Convert back to PIL Image
    customized_img = Image.fromarray(img_array)
    
    # Resize if requested
    if size_pixels > 0:
        customized_img = customized_img.resize((size_pixels, size_pixels), Image.NEAREST)
    
    return customized_img