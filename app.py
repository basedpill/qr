from flask import Flask, render_template, request
from PIL import Image
import os
from qr_main import QR_Code
from customisation import apply_customization
import numpy as np

app = Flask(__name__)

OUTPUT_IMAGE_PATH = os.path.join("static", "qr.png")

@app.route('/', methods=['GET', 'POST'])
def index():
    qrGenerated = False
    error = None
    showSteps = False
    stepsAvailable = False
    step_files = []

    if request.method == 'POST':
        inputText = request.form.get('textInput')
        color_hex = request.form.get('colorPicker', '#000000')
        size_input = request.form.get('sizeInput', '500')
        showSteps = request.form.get('showSteps') == 'on'

        if inputText:
            try:
                try:
                    custom_size = int(size_input)
                except ValueError:
                    custom_size = 0
                
                qrObject = QR_Code(inputText, "L")
                base_img = qrObject.Get_QR_Image()
                
                customized_img = apply_customization(
                    base_img, 
                    color_hex=color_hex,
                    size_pixels=custom_size if custom_size > 0 else base_img.width * 10
                )
                
                customized_img.save("static/qr.png")
                qrGenerated = True
                
                if showSteps:
                    try:
                        steps = qrObject.Get_QR_Generation_Steps(scale=10)
                        
                        step_files = []
                        for i, img in enumerate(steps):
                            filename = f"step_{i+1}.png"
                            img_path = os.path.join("static", filename)
                            img.save(img_path)
                            step_files.append(filename)
                        
                        stepsAvailable = True
                    except Exception as e:
                        error = f"Error generating steps: {str(e)}"
                
            except Exception as e:
                error = f"Error generating QR: {str(e)}"
        else:
            error = "Please enter a valid string."

    return render_template(
        'index.html', 
        qrGenerated=qrGenerated,
        showSteps=showSteps,
        stepsAvailable=stepsAvailable,
        step_files=step_files,
        error=error
    )

if __name__ == '__main__':
    app.run(debug=True)