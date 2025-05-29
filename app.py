from flask import Flask, render_template, request
import os
from qr_main import QR_Code
from customisation import apply_customization

app = Flask(__name__)

OUTPUT_IMAGE_PATH = os.path.join("static", "qr.png")

@app.route('/', methods=['GET', 'POST'])
def index():
    qrGenerated = False
    error = None
    showSteps = False
    stepsAvailable = False
    stepFiles = []

    if request.method == 'POST':
        inputText = request.form.get('textInput')
        colorHex = request.form.get('colorPicker', '#000000')
        sizeInput = request.form.get('sizeInput', '500')
        showSteps = request.form.get('showSteps') == 'on'

        if inputText:
            try:
                try:
                    customSize = int(sizeInput)
                except ValueError:
                    customSize = 0
                
                qrObject = QR_Code(inputText, "L")
                baseImg = qrObject.Get_QR_Image()
                
                customizedImg = apply_customization(
                    baseImg, 
                    colorHex,
                    customSize if customSize > 0 else baseImg.width * 10
                )
                
                customizedImg.save("static/qr.png")
                qrGenerated = True
                
                if showSteps:
                    try:
                        steps = qrObject.Get_QR_Generation_Steps(scale=10)
                        stepFiles = []

                        for i, img in enumerate(steps):
                            filename = f"step_{i+1}.png"
                            imgPath = os.path.join("static", filename)
                            img.save(imgPath)
                            stepFiles.append(filename)
                        
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
        stepFiles=stepFiles,
        error=error
    )

if __name__ == '__main__':
    app.run(debug=True)