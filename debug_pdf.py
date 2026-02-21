import os
import subprocess
import tempfile
import shutil

def debug_pdf():
    print("--- Edge PDF FINAL TEST (Temp Folder Strategy) ---")
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    # 1. Kendi Temp klasorumuzu olusturalim
    # Boylece OneDrive engelinden kurtuluruz
    base_temp = tempfile.gettempdir()
    my_temp = os.path.join(base_temp, "po_gen_temp")
    if not os.path.exists(my_temp): os.makedirs(my_temp)
    
    tmp_html = os.path.join(my_temp, "in.html")
    tmp_pdf = os.path.join(my_temp, "out.pdf")
    
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write("<html><body><h1>TEMP STRATEGY SUCCESS</h1></body></html>")
    
    # URL'i tam olarak Edge'in istedigi gibi olusturalim
    file_url = "file:///" + os.path.abspath(tmp_html).replace("\\", "/")
    print(f"URL: {file_url}")
    print(f"Dest: {tmp_pdf}")

    # 2. Komutu calistir
    cmd = [
        edge,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        f"--print-to-pdf={tmp_pdf}",
        file_url
    ]
    
    print("\nEdge calistiriliyor...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDERR:", result.stderr)
    
    # 3. Kontrol
    if os.path.exists(tmp_pdf):
        print(f"\nMUJDE! PDF olusturuldu. Boyut: {os.path.getsize(tmp_pdf)}")
        # Artik asil klasore tasiyabiliriz
        final_dest = os.path.abspath("SUCCESS_TEST.pdf")
        shutil.move(tmp_pdf, final_dest)
        print(f"Dosya OneDrive klasorune tasindi: {final_dest}")
    else:
        print("\nMAALESEF! Edge bu sefer de dosya yazamadi.")

if __name__ == "__main__":
    debug_pdf()
