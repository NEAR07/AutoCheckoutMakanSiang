from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
import os
import datetime

# 1. Deteksi Semua Akun dari Environment Variables
accounts = []
i = 1
while True:
    nip = os.getenv(f"LOGIN_NIP_{i}")
    password = os.getenv(f"PASSWORD_NIP_{i}")
    if nip and password:
        accounts.append({"nip": nip, "pass": password})
        i += 1
    else:
        break

if not accounts:
    raise ValueError("ERROR: Tidak ada kredensial akun yang terdeteksi di Secrets GitHub!")

print(f"Total akun yang akan diproses: {len(accounts)}")

# 2. Fungsi Utama Proses Pesanan per Akun
def proses_pesanan_akun(nip, password):
    print(f"\n==========================================")
    print(f"MEMPROSES AKUN: {nip}")
    print(f"==========================================")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.page_load_strategy = 'eager'

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    wait = WebDriverWait(driver, 15)

    try:
        # FASE 1: LOGIN
        print("Membuka halaman login...")
        try:
            driver.get("https://makan.sdm-pal.web.id/login")
        except Exception:
            print("Peringatan: Page load timeout, melanjutkan eksekusi DOM...")

        print("Mengisi kredensial...")
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(nip)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        time.sleep(3)

        # FASE 2: NAVIGASI KE HALAMAN PESANAN
        current_month = datetime.datetime.now().strftime("%Y-%m")
        target_url = f"https://makan.sdm-pal.web.id/portal/order?meal_type=makan_siang&month={current_month}"
        print(f"Navigasi ke halaman pesanan: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception:
            print("Peringatan: Page load timeout saat navigasi, melanjutkan...")

        # FASE 3: EKSTRAKSI & PROSES TANGGAL KOSONG
        print("Mencari tanggal yang belum dipesan...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-date]")))
        
        unordered_dates_xpath = "//div[contains(@class, 'bg-white') and @data-date]"
        unordered_elements = driver.find_elements(By.XPATH, unordered_dates_xpath)
        
        target_dates = [el.get_attribute("data-date") for el in unordered_elements if el.get_attribute("data-date")]
        
        if not target_dates:
            print(f"Semua pesanan minggu ini untuk NIP {nip} sudah terisi!")
        else:
            print(f"Ditemukan {len(target_dates)} hari belum dipesan untuk NIP {nip}: {target_dates}")
            
            for tgl in target_dates:
                try:
                    print(f"Memproses tanggal: {tgl}")
                    date_xpath = f"//div[@data-date='{tgl}']"
                    date_el = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_el)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", date_el)
                    
                    btn_pesan_xpath = "//button[.//span[contains(text(), 'Pesan Sekarang')]]"
                    pesan_sekarang_btn = wait.until(EC.presence_of_element_located((By.XPATH, btn_pesan_xpath)))
                    
                    driver.execute_script("arguments[0].click();", pesan_sekarang_btn)
                    print(f"-> Berhasil pesan tanggal {tgl}")
                    time.sleep(3) 
                    
                except Exception:
                    print(f"x Gagal memproses tanggal {tgl}")
                    print(traceback.format_exc())

    finally:
        print(f"Selesai memproses akun {nip}.")
        driver.quit()

# 3. Eksekusi Perulangan untuk Semua Akun
for acc in accounts:
    proses_pesanan_akun(acc["nip"], acc["pass"])
