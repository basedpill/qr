# app.py
from flask import Flask, render_template, request
from PIL import Image
import os
from qr_main import QR_Code
import numpy as np
from customisation import apply_customization  # Import the customizer

app = Flask(__name__)

OUTPUT_IMAGE_PATH = os.path.join("static", "qr.png")

@app.route('/', methods=['GET', 'POST'])
def index():
    qrGenerated = False
    error = None

    if request.method == 'POST':
        inputText = request.form.get('textInput')
        color_hex = request.form.get('colorPicker', '#000000')  # Default to black
        size_input = request.form.get('sizeInput', '0')  # Default to 0 (no custom size)

        if inputText:
            try:
                # Get custom size or default to 0
                try:
                    custom_size = int(size_input)
                except ValueError:
                    custom_size = 0
                
                qrObject = QR_Code(inputText, "L")
                
                # Get the QR image instead of saving immediately
                base_img = qrObject.Get_QR_Image()
                
                # Apply customization
                customized_img = apply_customization(
                    base_img, 
                    color_hex=color_hex,
                    size_pixels=custom_size if custom_size > 0 else base_img.width * 10
                )
                
                # Save the customized image
                customized_img.save("static/qr.png")
                
                qrGenerated = True
            except Exception as e:
                error = f"Error generating QR: {str(e)}"
        else:
            error = "Please enter a valid string."

    return render_template('index.html', qrGenerated=qrGenerated, error=error)

if __name__ == '__main__':
    app.run(debug=True)