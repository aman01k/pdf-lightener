import io
import fitz
import streamlit as st
from PIL import Image

st.set_page_config(page_title="PDF Lightener", layout="wide")

st.title("📄 PDF Background Lightener")
st.write("Upload a PDF with dark backgrounds and download a printer-friendly version.")


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


def convert_image(img):
    """
    Black (or near-black) -> White
    White (or near-white) -> Light Gray
    Everything else -> Unchanged
    """

    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size

    BLACK_THRESHOLD = 40  # 0-255
    WHITE_THRESHOLD = 240  # 0-255
    LIGHT_GRAY = 235

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Near black
            if r <= BLACK_THRESHOLD and g <= BLACK_THRESHOLD and b <= BLACK_THRESHOLD:
                pixels[x, y] = (255, 255, 255)

            # Near white
            elif r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD:
                pixels[x, y] = (LIGHT_GRAY, LIGHT_GRAY, LIGHT_GRAY)

            # Else: leave unchanged

    return img


uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    output = fitz.open()

    total_pages = len(pdf)

    page_range = st.text_input(
        "Pages to convert",
        value=f"1-{total_pages}",
        help="Examples: 1-10, 5-20, 8, 1-5,8,10-15",
    )

    if st.button("Convert PDF"):
        pages_to_convert = parse_page_range(page_range, total_pages)

        if pages_to_convert is None or len(pages_to_convert) == 0:
            st.error("Invalid page range.")
            st.stop()

        pages_to_convert = set(pages_to_convert)

        progress = st.progress(0)

        for i, page in enumerate(pdf):
            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False,
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            if i in pages_to_convert:
                img = convert_image(img)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)

            rect = fitz.Rect(0, 0, pix.width, pix.height)

            new_page = output.new_page(
                width=pix.width,
                height=pix.height,
            )

            new_page.insert_image(
                rect,
                stream=buffer.getvalue(),
            )

            progress.progress((i + 1) / total_pages)

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
