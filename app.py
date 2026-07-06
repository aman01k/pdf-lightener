import io
import fitz
import streamlit as st
from PIL import Image, ImageOps

st.set_page_config(page_title="PDF Lightener", layout="wide")

st.title("📄 PDF Background Lightener")
st.write("Upload a PDF with dark backgrounds and download a printer-friendly version.")

uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    output = fitz.open()

    progress = st.progress(0)

    for i, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples,
        )

        # Invert colors
        img_array = np.array(img)

        # Calculate brightness of every pixel
        brightness = img_array.mean(axis=2)

        # Threshold for dark pixels
        threshold = 50

        # Only convert dark pixels to white
        img_array[brightness < threshold] = [255, 255, 255]

        # Convert back to PIL image
        img = Image.fromarray(img_array)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)

        rect = fitz.Rect(0, 0, pix.width, pix.height)

        new_page = output.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(rect, stream=buffer.getvalue())

        progress.progress((i + 1) / len(pdf))

    result = io.BytesIO()
    output.save(result)
    result.seek(0)

    st.success("Done!")

    st.download_button(
        "⬇ Download Converted PDF",
        data=result,
        file_name="light_background.pdf",
        mime="application/pdf",
    )
