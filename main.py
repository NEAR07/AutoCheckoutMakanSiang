from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

# 1. Konfigurasi Browser
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # Jalankan di background jika sudah stabil
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

try:
    # ==========================================
    # FASE 1: LOGIN
    # ==========================================
    print("Membuka halaman login...")
    driver.get("https://makan.sdm-pal.web.id/login")

    print("Mengisi kredensial...")
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_field.send_keys("LOGIN_NIP_1") # Ganti NIP

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys("PASSWORD_NIP_1")   # Ganti Password

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    
    time.sleep(3) # Tunggu sesi login tersimpan

    # ==========================================
    # FASE 2: NAVIGASI KE HALAMAN PESANAN
    # ==========================================
    target_url = "https://makan.sdm-pal.web.id/portal/order?meal_type=makan_siang&month=2026-08"
    print(f"Navigasi ke halaman pesanan: {target_url}")
    driver.get(target_url)

    # ==========================================
    # FASE 3: EKSTRAKSI & PROSES TANGGAL KOSONG
    # ==========================================
    print("Mencari tanggal yang belum dipesan...")
    unordered_dates_xpath = "//div[contains(@class, 'bg-white') and @data-date]" 
    
    # Ambil semua elemen yang masih bg-white
    unordered_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, unordered_dates_xpath)))
    
    # Ekstrak 'data-date' masing-masing ke dalam list agar kebal dari perubahan DOM (Stale Element)
    target_dates = [el.get_attribute("data-date") for el in unordered_elements]
    
    if not target_dates:
        print("Semua pesanan untuk bulan ini sudah terisi!")
    else:
        print(f"Ditemukan {len(target_dates)} hari yang belum dipesan: {target_dates}")
        
        # Eksekusi pesanan per tanggal
        for tgl in target_dates:
            try:
                print(f"\nMemproses pesanan untuk tanggal: {tgl}")
                
                date_xpath = f"//div[@data-date='{tgl}']"
                # Ubah ke presence_of_element_located karena div kadang gagal melewati validasi clickable Selenium
                date_el = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
                
                # Scroll ke elemen
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_el)
                time.sleep(1)
                
                # KLIK MENGGUNAKAN JAVASCRIPT (Mencegah ElementClickIntercepted)
                driver.execute_script("arguments[0].click();", date_el)
                
                print("Menunggu pop-up muncul...")
                btn_pesan_xpath = "//button[.//span[contains(text(), 'Pesan Sekarang')]]"
                pesan_sekarang_btn = wait.until(EC.presence_of_element_located((By.XPATH, btn_pesan_xpath)))
                
                # Klik tombol di pop-up juga menggunakan JavaScript untuk memastikan
                driver.execute_script("arguments[0].click();", pesan_sekarang_btn)
                print(f"Berhasil mengklik pesan untuk tanggal {tgl}.")
                
                time.sleep(3) 
                
            except Exception as e:
                print(f"Gagal memproses pesanan untuk {tgl}.")
                # Ini akan mencetak detail baris kode mana yang menyebabkan error
                print(traceback.format_exc())

finally:
    print("Script automasi selesai dieksekusi.")
    # driver.quit() # Hapus tanda pagar untuk menutup Chrome otomatis
