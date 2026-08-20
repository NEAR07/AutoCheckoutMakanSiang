from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
import os
import datetime

# 1. Kredensial
LOGIN_NIP = os.getenv("LOGIN_NIP", "LOGIN_NIP_1")
LOGIN_PASS = os.getenv("LOGIN_PASS", "PASSWORD_NIP_1")

# 2. Konfigurasi Browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

try:
    # FASE 1: LOGIN
    print("Membuka halaman login...")
    driver.get("https://makan.sdm-pal.web.id/login")

    print("Mengisi kredensial...")
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_field.send_keys(LOGIN_NIP)

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(LOGIN_PASS)

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    
    time.sleep(3)

    # FASE 2: NAVIGASI KE HALAMAN PESANAN
    current_month = datetime.datetime.now().strftime("%Y-%m")
    target_url = f"https://makan.sdm-pal.web.id/portal/order?meal_type=makan_siang&month={current_month}"
    print(f"Navigasi ke halaman pesanan: {target_url}")
    driver.get(target_url)

    # FASE 3: EKSTRAKSI & PROSES TANGGAL KOSONG
    print("Mencari tanggal yang belum dipesan...")
    
    # Tunggu minimal 1 elemen tanggal termuat di halaman (baik bg-green atau bg-white)
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-date]")))
    
    # Menggunakan find_elements agar aman mengembalikan [] tanpa TimeoutException
    unordered_dates_xpath = "//div[contains(@class, 'bg-white') and @data-date]"
    unordered_elements = driver.find_elements(By.XPATH, unordered_dates_xpath)
    
    target_dates = [el.get_attribute("data-date") for el in unordered_elements if el.get_attribute("data-date")]
    
    if not target_dates:
        print("Semua pesanan untuk bulan ini sudah terisi!")
    else:
        print(f"Ditemukan {len(target_dates)} hari yang belum dipesan: {target_dates}")
        
        for tgl in target_dates:
            try:
                print(f"\nMemproses pesanan untuk tanggal: {tgl}")
                
                date_xpath = f"//div[@data-date='{tgl}']"
                date_el = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_el)
                time.sleep(1)
                
                driver.execute_script("arguments[0].click();", date_el)
                
                print("Menunggu pop-up muncul...")
                btn_pesan_xpath = "//button[.//span[contains(text(), 'Pesan Sekarang')]]"
                pesan_sekarang_btn = wait.until(EC.presence_of_element_located((By.XPATH, btn_pesan_xpath)))
                
                driver.execute_script("arguments[0].click();", pesan_sekarang_btn)
                print(f"Berhasil mengklik pesan untuk tanggal {tgl}.")
                
                time.sleep(3) 
                
            except Exception as e:
                print(f"Gagal memproses pesanan untuk {tgl}.")
                print(traceback.format_exc())

finally:
    print("Script automasi selesai dieksekusi.")
    driver.quit()
