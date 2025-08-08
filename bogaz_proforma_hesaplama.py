# Boğaz geçişi hesaplama motoru - Genişletilmiş (Streamlit arayüzlü)
import math
import pandas as pd
import streamlit as st

# Excel dosyasından tarifeleri yükle
excel_yolu = "Tarife_Sablonu.xlsx"
kilavuzluk_df = pd.read_excel(excel_yolu, sheet_name="kilavuzluk")
romorkor_ist_df = pd.read_excel(excel_yolu, sheet_name="romorkor_istanbul")
romorkor_can_df = pd.read_excel(excel_yolu, sheet_name="romorkor_canakkale")
sabitler_df = pd.read_excel(excel_yolu, sheet_name="sabit_kalemler")

# Fonksiyonlar
def hesapla_saglik_resmi(nrt):
    katsayi = 0.43725
    return round(katsayi * nrt, 2)

def hesapla_fener_ucreti(nrt, tarife, ugraksiz):
    if ugraksiz:
        ilk_800 = min(nrt, 800) * 2.4486
        kalan = max(0, nrt - 800) * 1.2243
        return round(ilk_800 + kalan, 2)
    else:
        return 0.0

def hesapla_tahlisiye_ucreti(nrt, tarife, ugraksiz):
    if ugraksiz:
        return round(nrt * 0.583, 2)
    else:
        return 0.0

def hesapla_kilavuzluk(grt, hizmet):
    # Sadeleştirilmiş örnek hesaplama (örnek 2: İstanbul Boğaz geçişi)
    base = 550
    ek = math.ceil(max(grt - 1000, 0) / 1000) * 100
    return round(base + ek, 2)

def hesapla_acente_ucreti(nrt):
    if nrt <= 1000:
        return 200
    elif nrt <= 2000:
        return 290
    elif nrt <= 3000:
        return 340
    elif nrt <= 4000:
        return 400
    elif nrt <= 5000:
        return 460
    elif nrt <= 7500:
        return 560
    elif nrt <= 10000:
        return 640
    elif nrt <= 20000:
        return 640 + ((nrt - 10000) // 1000) * 30
    elif nrt <= 30000:
        return 640 + (10 * 30) + ((nrt - 20000) // 1000) * 20
    else:
        return 640 + (10 * 30) + (10 * 20) + ((nrt - 30000) // 1000) * 10

def hesapla_acente_refakatli(acente_ucreti, refakat):
    return acente_ucreti * 1.3 if refakat else acente_ucreti

def hesapla_romorkor(boy, cins, bogaz):
    if bogaz == "istanbul":
        df = romorkor_ist_df
    else:
        df = romorkor_can_df
    for i, row in df.iterrows():
        min_boy = row['min_boy']
        max_boy = row['max_boy']
        if min_boy <= boy <= max_boy and row['cins'].strip().lower() in cins.strip().lower():
            return row['ucret']
    return 0

# Kullanıcı seçimlerini yansıtan durumları al
st.set_page_config(layout="wide")
st.title("Boğaz Geçişi Proforma Hesaplama")

with st.expander("🔧 Gemi Bilgileri ve Parametreler", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        nrt = st.number_input("NRT (Net Register Tonnage)", value=1500)
        grt = st.number_input("GRT (Gross Register Tonnage)", value=2500)
        boy = st.number_input("Gemi Boyu (metre)", value=180.0)

    with col2:
        cins = st.selectbox("Gemi Cinsi", ["TANKER", "LPG", "NÜKLEER", "TANKER/LPG", "LPG/ NÜKLEER", "RO-RO/KONT /DİGER"])
        gecis_turu = st.selectbox(
            "Geçiş Türü",
            [
                "1 - Full Transit Geçiş",
                "2 - Marmara In",
                "3 - Marmara Out",
                "4 - Çanakkale In",
                "5 - Çanakkale Out",
                "6 - Serbest Geçiş"
            ]
        )
        ugraksiz_mi = st.radio("Uğraksız (transit) geçiş mi?", ["Evet", "Hayır"], index=1) == "Evet"

    with col3:
        usd_try_kur = st.number_input("USD/TRY kuru", value=32.5)
        eur_usd_kur = st.number_input("EUR/USD kuru", value=1.08)
        refakat_var = st.checkbox("Refakatli geçiş mi?", value=True)
        turk_bayrakli = st.checkbox("Türk bayraklı mı?", value=False)
        kabotaj_mi = st.checkbox("Kabotaj seferi mi?", value=False)
        yolcu_gemisi_mi = st.checkbox("Yolcu gemisi mi?", value=False)

# Boğaz yönü belirleme
bogaz_gecir = []
if "full" in gecis_turu.lower():
    bogaz_gecir = ["çanakkale", "istanbul"]
elif "marmara in" in gecis_turu.lower():
    bogaz_gecir = ["çanakkale"]
elif "marmara out" in gecis_turu.lower():
    bogaz_gecir = ["istanbul"]
elif "çanakkale in" in gecis_turu.lower():
    bogaz_gecir = ["çanakkale"]
elif "çanakkale out" in gecis_turu.lower():
    bogaz_gecir = ["çanakkale"]
elif "serbest" in gecis_turu.lower():
    bogaz_gecir = []

# Tarifeyi belirle
tarife_kodu = "yabanci"
if kabotaj_mi:
    tarife_kodu = "kabotaj"
elif turk_bayrakli:
    tarife_kodu = "turk"
elif yolcu_gemisi_mi:
    tarife_kodu = "yolcu"

# Hesaplama
if st.button("Hesapla"):
    saglik = hesapla_saglik_resmi(nrt)
    fener = hesapla_fener_ucreti(nrt, tarife_kodu, ugraksiz_mi)
    tahlisiye = hesapla_tahlisiye_ucreti(nrt, tarife_kodu, ugraksiz_mi)
    kilavuz = hesapla_kilavuzluk(grt, "bogaz_gecisi")
    acente_eur = hesapla_acente_ucreti(nrt)
    acente = round(acente_eur * eur_usd_kur, 2)
    acente_refakat = hesapla_acente_refakatli(acente_eur, refakat_var)
    acente_refakat_usd = round(acente_refakat * eur_usd_kur, 2)

    romorkor_toplam = 0.0
    for b in bogaz_gecir:
        romorkor_toplam += hesapla_romorkor(boy, cins, b)

    st.subheader("Hesaplama Sonuçları (USD):")
    st.write(f"Sağlık Resmi: {saglik} USD")
    st.write(f"Fener Ücreti: {fener} USD")
    st.write(f"Tahlisiye Ücreti: {tahlisiye} USD")
    st.write(f"Kılavuzluk Ücreti: {kilavuz} USD")
    st.write(f"Acentelik Ücreti: {acente} USD")
    st.write(f"Refakatli Geçiş Ek Acentelik Ücreti: {acente_refakat_usd} USD")
    st.write(f"Römorkör Ücreti (Toplam): {romorkor_toplam} USD")
