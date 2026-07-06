import io
import fitz
import streamlit as st
import numpy as np
from PIL import Image

st.set_page_config(page_title="PDF Lightener", layout="wide")

st.title("📄 PDF Background Lightener")
st.write(
    "Convert only the dark backgrounds of selected PDF pages into printer-friendly white backgrounds."
)


def parse_page_range(page_range, total_pages):
    pages = set()

    try:
        for part in page_range.split(","):
            part = part.strip()

            if "-" in part:
                start, end = part.split("-")
                start = max(1, int(start))
                end = min(total_pages, int(end))
                pages.update(range(start - 1, end))

            else:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages.add(page - 1)

    except ValueError:
        return None

    return sorted(pages)


uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(pdf)

    st.success(f"PDF Loaded ({total_pages} pages)")

    page_range = st.text_input(
        "Pages to convert",
        value=f"1-{total_pages}",
        help="Examples: 1-10, 5-20, 8, 1-5,8,10-15",
    )

    threshold = st.slider(
        "Darkness Threshold",
        min_value=20,
        max_value=120,
        value=70,
        help="Higher values remove more dark shades.",
    )

    if st.button("Convert PDF"):
        pages_to_convert = parse_page_range(page_range, total_pages)

        if pages_to_convert is None or len(pages_to_convert) == 0:
            st.error("Invalid page range.")
            st.stop()

        pages_to_convert = set(pages_to_convert)

        output = fitz.open()

        progress = st.progress(0)

        for page_index in range(total_pages):
            page = pdf.load_page(page_index)

            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False,
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            # Convert only selected pages
            if page_index in pages_to_convert:
                img_array = np.array(img)

                brightness = img_array.mean(axis=2)

                img_array[brightness < threshold] = [255, 255, 255]

                img = Image.fromarray(img_array)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)

            rect = fitz.Rect(0, 0, pix.width, pix.height)

            new_page = output.new_page(
                width=pix.width,
                height=pix.height,
            )

            new_page.insert_image(
                rect,
                stream=buffer.getvalue(),
            )

            progress.progress((page_index + 1) / total_pages)

        result = io.BytesIO()
        output.save(result)
        result.seek(0)

        st.success("✅ Conversion Complete!")

        st.download_button(
            "⬇ Download Converted PDF",
            data=result,
            file_name="light_background.pdf",
            mime="application/pdf",
        )
