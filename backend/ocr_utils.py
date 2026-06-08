import fitz
import numpy as np

from PIL import Image
from rapidocr_onnxruntime import RapidOCR


ocr_engine = RapidOCR()


def ocr_page(page):

    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2)
    )

    img = Image.fromarray(
        np.frombuffer(
            pix.samples,
            dtype=np.uint8
        ).reshape(
            pix.height,
            pix.width,
            pix.n
        )
    )

    result, _ = ocr_engine(
        np.array(img)
    )

    if result is None:
        return ""

    extracted_text = []

    for item in result:
        extracted_text.append(
            item[1]
        )

    return "\n".join(
        extracted_text
    )