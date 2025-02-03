import os
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import xml.etree.ElementTree as ET
import win32com.client as win32
import zipfile
import re
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def extract_text_from_txt(file_path):
    """Extracts text from a .txt file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

### Old Function (works quite well for most PDFs) ####
def extract_text_from_pdf(file_path):
    """Extracts text from a .pdf file using pdfplumber with layout=True."""
    extracted_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # The key difference: pass layout=True
            page_text = page.extract_text(layout=True) or ""
            extracted_text.append(page_text)
    # Join all pages
    raw_text = "\n".join(extracted_text)

    # Optional: post-process to fix line breaks 
    processed_text = fix_line_breaks(raw_text)
    return processed_text

def fix_line_breaks(text):
    """
    Naive approach to merge lines that shouldn't be separate.
    For example, if a line does not end in punctuation
    and the next line starts with a lowercase letter.
    """
    lines = text.split("\n")
    merged_lines = []
    skip_next = False
    for i in range(len(lines)):
        if skip_next:
            skip_next = False
            continue
        line = lines[i].strip()
        if i < len(lines) - 1:
            next_line = lines[i+1].strip()
            # If line does not end in common punctuation and next line starts lower
            if (not re.search(r'[.!?;:\)]$', line) 
                and len(next_line) > 0 
                and next_line[0].islower()):
                # Merge them
                line = line + " " + next_line
                skip_next = True
        merged_lines.append(line)
    return "\n".join(merged_lines)

def check_bboxes_overlap_or_distance(bboxes, 
                                     page_width, 
                                     overlap_threshold=0.3, # % box width | High overlap_threshold => they need to overlap a lot before reverting to one column. | Low overlap_threshold => even a moderate overlap is enough to consider it “single column.”
                                     gap_threshold=0.05):   # % of page   | High gap_threshold => more “strict” about needing a wide gap to confirm two columns. | Low gap_threshold => more “lenient” about small gaps, so you’re less likely to revert to a single column.
    """
    Suppose bboxes is a list of two bounding boxes: [(x0a,0,x1a,h), (x0b,0,x1b,h)] 
    sorted left-to-right.  We'll see if they truly look like two columns.
    
    overlap_threshold: If they overlap horizontally more than this fraction of average box width
    gap_threshold: If the horizontal gap is less than this fraction of the page width
    """
    if len(bboxes) != 2:
        return False  # If not exactly 2, no check needed (could be 1 or 3)

    (x0a, _, x1a, _) = bboxes[0]
    (x0b, _, x1b, _) = bboxes[1]

    # 1) Overlap check
    overlap_width = max(0, min(x1a, x1b) - max(x0a, x0b))
    box_a_width = x1a - x0a
    box_b_width = x1b - x0b
    avg_box_width = (box_a_width + box_b_width) / 2.0

    if overlap_width > overlap_threshold * avg_box_width:
        # They overlap too much => probably a single column
        return True

    # 2) Gap check (distance between right edge of A and left edge of B)
    gap_width = x0b - x1a  
    if gap_width < gap_threshold * page_width:
        # Gap is too small => probably single column
        return True

    return False

def detect_columns_kmeans(
    page, 
    k_values=(1, 2),
    min_silhouette=0.2,      # minimum silhouette for "valid" multi-column
    min_cluster_ratio=0.05   # smallest ratio of words in any column
):
    """
    Dynamically detect how many columns a page might have using K-means on the x-midpoints.
    Additional heuristics:
      - If the best silhouette < min_silhouette, revert to k=1
      - If the smaller cluster ratio < min_cluster_ratio, revert to k=1
    """
    words = page.extract_words()
    if not words:
        return []

    # Calculate x-mid for each word
    x_mids = np.array([((w["x0"] + w["x1"]) / 2) for w in words]).reshape(-1, 1)
    
    best_k = 1
    best_score = -1  # silhouette ranges [-1..1], start below
    
    # 1) Try each k in k_values, compute silhouette
    for k in k_values:
        if k > len(x_mids):
            # can't cluster into more clusters than points
            continue
        kmeans = KMeans(n_clusters=k, random_state=42).fit(x_mids)
        labels = kmeans.labels_
        
        # silhouette is undefined for k=1
        if k == 1:
            # treat single column as “neutral” baseline
            continue
        else:
            score = silhouette_score(x_mids, labels)
            if score > best_score:
                best_score = score
                best_k = k

    # 2) Re-run KMeans with best_k
    if best_k == 1:
        # only one cluster => entire page is one column
        bboxes = [(0, 0, page.width, page.height)]
        return bboxes

    kmeans = KMeans(n_clusters=best_k, random_state=42).fit(x_mids)
    labels = kmeans.labels_
    final_score = silhouette_score(x_mids, labels)

    # --- Heuristic #1: silhouette threshold ---
    if final_score < min_silhouette:
        # revert to 1 column
        return [(0, 0, page.width, page.height)]
    
    # --- Heuristic #2: cluster ratio check ---
    cluster_sizes = [np.sum(labels == c) for c in range(best_k)]
    smallest_cluster_size = min(cluster_sizes)
    total_size = len(x_mids)
    ratio = smallest_cluster_size / total_size
    if ratio < min_cluster_ratio:
        # revert to 1 column
        return [(0, 0, page.width, page.height)]
    
    # 3) We accept best_k as is, build bounding boxes
    bboxes = []
    for cluster_id in range(best_k):
        cluster_words = [w for w, lbl in zip(words, labels) if lbl == cluster_id]
        if not cluster_words:
            continue
        
        min_x = min(w["x0"] for w in cluster_words)
        max_x = max(w["x1"] for w in cluster_words)
        bbox = (min_x, 0, max_x, page.height)
        bboxes.append(bbox)
    
    # Sort bounding boxes left-to-right
    bboxes_sorted = sorted(bboxes, key=lambda b: b[0])
    
    # 4) (Optional) bounding-box overlap/distance check
    if len(bboxes_sorted) == 2:
        if check_bboxes_overlap_or_distance(bboxes_sorted, page.width):
            bboxes_sorted = [(0, 0, page.width, page.height)]

    return bboxes_sorted

def extract_text_dynamic_kmeans(file_path):
    all_pages_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # 1) Detect columns on this page
            col_bboxes = detect_columns_kmeans(page, k_values=(1, 2))
            
            # If we found no words, skip
            if not col_bboxes:
                continue
            
            # 2) For each column bounding box, crop + extract text
            page_cols_text = []
            for bbox in col_bboxes:
                crop = page.crop(bbox)
                # Use layout=True to preserve some horizontal spacing
                col_text = crop.extract_text(layout=True) or ""
                page_cols_text.append(col_text)
            
            # 3) Join all columns in left-to-right reading order
            page_text = "\n".join(page_cols_text)
            all_pages_text.append(page_text)

    # 4) Combine text across all pages
    raw_text = "\n\n".join(all_pages_text)
    # 5) Optionally fix line breaks
    processed_text = fix_line_breaks(raw_text)
    
    return processed_text.strip()

# Namespaces commonly used in WordprocessingML
# We'll need these to properly search for elements in the XML
namespaces = {
    'w':  'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':  'http://schemas.openxmlformats.org/drawingml/2006/main',
    'v':  'urn:schemas-microsoft-com:vml',
    'wps':'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
}

def extract_text_from_docx(file_path):
    """
    Extracts text from a .docx file, including:
      - Normal paragraph text
      - Text contained in shapes, text boxes, or grouped shapes
    """

    # 1) Extract MAIN BODY TEXT via python-docx
    doc = Document(file_path)
    text_parts = []

    # Grab normal paragraph text
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # 2) Extract TEXT FROM SHAPES / TEXT BOXES by parsing the underlying XML
    #    We'll open the docx as a ZIP, iterate through relevant .xml files, and look for shape/textbox tags.
    with zipfile.ZipFile(file_path, 'r') as z:
        # Typical Word document parts of interest
        # - word/document.xml, word/headerX.xml, word/footerX.xml
        # - shape text might also appear in sub-parts or "drawings" directories
        xml_file_names = [
            name for name in z.namelist()
            if (
                name.startswith("word/") 
                and (name.endswith(".xml"))
                and not name.startswith("word/_rels")  # skip relationships
                and not name.startswith("word/theme")  # skip themes
            )
        ]

        for xml_name in xml_file_names:
            xml_content = z.read(xml_name)
            # Parse XML
            root = ET.fromstring(xml_content)

            # Look for text in <w:t> elements. Sometimes shapes and textboxes store text the same way.
            # We'll retrieve all <w:t> no matter where it lives (e.g. main doc, header, footer, shapes).
            for wt in root.findall(".//w:t", namespaces=namespaces):
                text_val = wt.text
                if text_val and text_val.strip():
                    text_parts.append(text_val)

            # Some older/alternate shapes might use VML: look for <v:shape> -> <w:p> -> <w:r> -> <w:t>
            # or <w:pict> -> ...
            for pict in root.findall(".//w:pict", namespaces=namespaces):
                # In VML shapes, text might still appear as w:t deeper inside
                for wt in pict.findall(".//w:t", namespaces=namespaces):
                    text_val = wt.text
                    if text_val and text_val.strip():
                        text_parts.append(text_val)

            # Office 2010+ shapes can appear under <wps:txbx> with <w:txbxContent> -> <w:p> -> <w:r> -> <w:t>
            for wps_txbx in root.findall(".//wps:txbx", namespaces=namespaces):
                for wt in wps_txbx.findall(".//w:t", namespaces=namespaces):
                    text_val = wt.text
                    if text_val and text_val.strip():
                        text_parts.append(text_val)
                        
    # Combine and return as a single string (or list, as needed)
    # Removing duplicates can be tricky: you might see repeated text from overlaps
    # in references, so you can optionally deduplicate if that’s an issue.
    unique_lines = []
    seen = set()
    for line in text_parts:
        line = line.strip()
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    return "\n".join(unique_lines)

def perform_ocr(file_path):
    """Performs OCR on an image file to extract text."""
    try:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"Error performing OCR on {file_path}: {e}")
        return ""

def process_cv(file_path):
    """
    Reads and processes a CV from file path.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        str: Contents of the file as string
    """
    def extract_text(file_path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == '.txt':
            return extract_text_from_txt(file_path)
        elif extension == '.pdf':
            return extract_text_dynamic_kmeans(file_path)
        elif extension == '.docx':
            return extract_text_from_docx(file_path)
        elif extension in ['.png', '.jpg', '.jpeg', '.tiff']:  # For image files
            return perform_ocr(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    text_content = extract_text(file_path)

    return text_content

def process_cover_letter(file_path):
    """
    Reads and processes a cover letter from file path.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        str: Contents of the file as string
    """
    def extract_text(file_path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == '.txt':
            return extract_text_from_txt(file_path)
        elif extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return extract_text_from_docx(file_path)
        elif extension in ['.png', '.jpg', '.jpeg', '.tiff']:  # For image files
            return perform_ocr(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    text_content = extract_text(file_path)

    return text_content.strip()