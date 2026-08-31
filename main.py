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
    
    driver = webdriver.Chrome(options=options)
    
    # PERBESAR TIMEOUT KARENA WEB MUNGKIN LAMBAT
    driver.set_page_load_timeout(60) 
    wait = WebDriverWait(driver, 20)

    try:
        # FASE 1: LOGIN
        print("Membuka halaman login...")
        driver.get("https://makan.sdm-pal.web.id/login")

        print("Mengisi kredensial...")
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(nip)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        time.sleep(3)

        # MENGHITUNG BULAN INI DAN BULAN DEPAN (DIPERBAIKI)
        now = datetime.datetime.now()
        current_month_str = now.strftime("%Y-%m")
        
        # Logika bulan depan (Set tanggal secara manual ke tanggal 1 agar terhindar dari error tanggal 31)
        if now.month == 12:
            next_month_date = datetime.datetime(now.year + 1, 1, 1)
        else:
            next_month_date = datetime.datetime(now.year, now.month + 1, 1)
            
        next_month_str = next_month_date.strftime("%Y-%m")

        months_to_process = [current_month_str, next_month_str]

        # LOOPING UNTUK BULAN INI DAN BULAN DEPAN
        for target_month in months_to_process:
            print(f"\n--- [ Mengecek Pesanan Untuk Bulan: {target_month} ] ---")
            
            # FASE 2: NAVIGASI KE HALAMAN PESANAN
            target_url = f"https://makan.sdm-pal.web.id/portal/order?meal_type=makan_siang&month={target_month}"
            print(f"Navigasi ke: {target_url}")
            driver.get(target_url)

            # FASE 3: EKSTRAKSI & PROSES TANGGAL KOSONG
            print(f"Mencari tanggal yang belum dipesan untuk {target_month}...")
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-date]")))
            except Exception:
                # Menangkap jika kalender bulan depan belum ada/belum di-generate oleh web
                print(f"Kalender untuk bulan {target_month} belum tersedia atau halaman kosong. Melewati...")
                continue
            
            unordered_dates_xpath = "//div[contains(@class, 'bg-white') and @data-date]"
            unordered_elements = driver.find_elements(By.XPATH, unordered_dates_xpath)
            
            target_dates = [el.get_attribute("data-date") for el in unordered_elements if el.get_attribute("data-date")]
            
            if not target_dates:
                print(f"Semua pesanan untuk bulan {target_month} sudah terisi penuh!")
            else:
                print(f"Ditemukan {len(target_dates)} hari belum dipesan pada {target_month}: {target_dates}")
                
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

    # BAGIAN PENANGANAN ERROR GLOBAL AKUN
    except Exception as e:
        print(f"⚠️ GAGAL memproses keseluruhan akun {nip}!")
        print(f"Detail Error: {str(e)}")
        
        # Simpan Screenshot & HTML untuk artifact GitHub Actions
        nama_file = f"error_akun_{nip}"
        try:
            driver.save_screenshot(f"{nama_file}.png")
            with open(f"{nama_file}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("📸 Screenshot & HTML halaman error berhasil disimpan. (Cek di tab Artifacts GitHub)")
        except Exception as ss_e:
            print(f"Gagal mengambil screenshot: {ss_e}")

    finally:
        print(f"Selesai memproses akun {nip}.")
        try:
            driver.quit()
        except:
            pass

# 3. Eksekusi Perulangan untuk Semua Akun
for acc in accounts:
    proses_pesanan_akun(acc["nip"], acc["pass"])
