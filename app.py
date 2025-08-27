import streamlit as st
from PIL import Image
import io

# -----------------------------------------
# Page setup
# -----------------------------------------
st.set_page_config(page_title="Image to PDF Converter", layout="wide")
st.title("🖼️ Image to PDF Converter")
st.write("Upload images in any format and convert them into a single PDF with your preferred quality.")

# -----------------------------------------
# File uploader
# -----------------------------------------
uploaded_files = st.file_uploader(
    "Upload image files",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    accept_multiple_files=True
)

# -----------------------------------------
# Load images and calculate total size
# -----------------------------------------
images = []
total_image_size_bytes = 0

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            img = Image.open(uploaded_file)
            # Ensure RGB for PDF
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)
            total_image_size_bytes += uploaded_file.size
        except Exception as e:
            st.error(f"Error loading image {uploaded_file.name}: {e}")

# -----------------------------------------
# Estimation helpers
# -----------------------------------------
QUALITY_PRESETS = {
    "High (300 DPI)": {"scale": 1.0, "dpi": 300},
    "Medium (150 DPI)": {"scale": 0.5, "dpi": 150},
    "Low (72 DPI)": {"scale": 0.25, "dpi": 72},
}

def estimate_pdf_size(total_bytes: int, scale: float) -> float:
    """
    Very rough estimate:
    - Scale factor approximates how much we downsample pixels before embedding in the PDF.
    - Actual size depends on image content, compression, and metadata.
    """
    return total_bytes * max(min(scale, 1.0), 0.05)  # Guardrails

# Precompute estimates for the UI
estimates = {
    label: estimate_pdf_size(total_image_size_bytes, preset["scale"])
    for label, preset in QUALITY_PRESETS.items()
}

# -----------------------------------------
# Quality & Compression (single choice)
# -----------------------------------------
with st.expander("🛠️ Quality & Compression", expanded=True):
    col1, col2, col3, col4 = st.columns([1,1,1,5])
    with col1:
        st.caption("High (300 DPI)")
        st.write(f"~ **{estimates['High (300 DPI)'] / (1024 * 1024):.2f} MB**")
    with col2:
        st.caption("Medium (150 DPI)")
        st.write(f"~ **{estimates['Medium (150 DPI)'] / (1024 * 1024):.2f} MB**")
    with col3:
        st.caption("Low (72 DPI)")
        st.write(f"~ **{estimates['Low (72 DPI)'] / (1024 * 1024):.2f} MB**")

    quality_choice = st.radio(
        "Choose a quality level",
        options=list(QUALITY_PRESETS.keys()),
        index=0,
        help="Higher quality = larger file size. Lower quality downscales images to reduce the PDF size.",
        horizontal=True,
    )

selected = QUALITY_PRESETS[quality_choice]
scale = selected["scale"]
dpi = selected["dpi"]
quality_label = quality_choice.split()[0]  # "High", "Medium", "Low"

# -----------------------------------------
# Convert to PDF
# -----------------------------------------
disabled = not bool(images)
if disabled:
    st.info("Upload at least one image to enable conversion.")

if st.button("Convert to PDF", type="primary", disabled=disabled):
    try:
        # Prepare (optionally downscale) images
        processed = []
        for im in images:
            if scale < 1.0:
                w, h = im.size
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                im_resized = im.resize(new_size, Image.LANCZOS)
                processed.append(im_resized)
            else:
                processed.append(im)

        # Save to a single PDF in memory
        pdf_bytes = io.BytesIO()
        # 'resolution' sets DPI metadata; size reduction mainly comes from downscaling above
        processed[0].save(
            pdf_bytes,
            format="PDF",
            save_all=True,
            append_images=processed[1:],
            resolution=dpi,
        )
        pdf_bytes.seek(0)

        st.success("✅ Conversion successful!")
        st.download_button(
            label=f"📥 Download PDF ({quality_label} Quality)",
            data=pdf_bytes.getvalue(),
            file_name="converted_images.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Conversion failed: {e}")
