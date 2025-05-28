from flask import Flask, render_template, request
from PIL import Image
import os
from StrToQR import QR_Code

app = Flask(__name__)

OUTPUT_IMAGE_PATH = os.path.join("static", "qr.png")

@app.route('/', methods=['GET', 'POST'])
def index():
    qrGenerated = False
    error = None

    if request.method == 'POST':
        inputText = request.form.get('textInput')

        if inputText:
            try:
                qrObject = QR_Code(inputText, "L")
                qrObject.Save_QR_Code(OUTPUT_IMAGE_PATH)

                img = Image.open(OUTPUT_IMAGE_PATH)
                newSize = (img.width * 10, img.height * 10)
                img = img.resize(newSize, Image.NEAREST)
                img.save(OUTPUT_IMAGE_PATH)

                qrGenerated = True
            except Exception as e:
                error = f"Error generating QR: {str(e)}"
        else:
            error = "Please enter a valid string."

    return render_template('index.html', qrGenerated=qrGenerated, qrPath=OUTPUT_IMAGE_PATH, error=error)

if __name__ == '__main__':
    app.run(debug=True)