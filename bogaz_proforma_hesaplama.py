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

# Kullanıcı seçimlerini yansıtan durumları al
st.set_page_config(layout="wide")
st.title("Boğaz Geçişi Proforma Hesaplama")

col1, col2, col3 = st.columns(3)

with col1:
    nrt = st.number_input("NRT (Net Register Tonnage)", value=1500)
    grt = st.number_input("GRT (Gross Register Tonnage)", value=2500)
    boy = st.number_input("Gemi Boyu (metre)", value=180.0)

with col2:
    cins = st.selectbox("Gemi Cinsi", ["TANKER", "LPG", "NÜKLEER", "TANKER/LPG", "LPG/ NÜKLEER", "RO-RO/KONT /DİGER"])
    bogaz = st.selectbox("Boğaz", ["istanbul", "çanakkale"])
    usd_try_kur = st.number_input("USD/TRY kuru", value=32.5)

with col3:
    eur_usd_kur = st.number_input("EUR/USD kuru", value=1.08)
    refakat_var = st.checkbox("Refakatli geçiş mi?", value=True)
    turk_bayrakli = st.checkbox("Türk bayraklı mı?", value=False)
    kabotaj_mi = st.checkbox("Kabotaj seferi mi?", value=False)
    ugraksiz_mi = st.checkbox("Uğraksız geçiş mi? (foreign to foreign)", value=True)
    yolcu_gemisi_mi = st.checkbox("Yolcu gemisi mi?", value=False)

# Tarifeyi belirle
tarife_kodu = "yabanci"
if kabotaj_mi:
    tarife_kodu = "kabotaj"
elif turk_bayrakli:
    tarife_kodu = "turk"
elif yolcu_gemisi_mi:
    tarife_kodu = "yolcu"

# Fonksiyonlar
def sabit_deger(kalem_adi):
    row = sabitler_df[sabitler_df["kalem"] == kalem_adi]
    return float(row["deger"].values[0]) if not row.empty else 0.0

def hesapla_saglik_resmi(nrt: float) -> float:
    katsayi = sabit_deger("saglik_katsayi")
    return round(katsayi * nrt, 2)

def hesapla_fener_ucreti(nrt: float, tarife: str, ugraksiz: bool) -> float:
    taban_kod = f"fener_{tarife}_ilk"
    ust_kod = f"fener_{tarife}_ust"
    if ugraksiz:
        taban = sabit_deger(taban_kod + "_ugraksiz")
        ust = sabit_deger(ust_kod + "_ugraksiz")
    else:
        taban = sabit_deger(taban_kod + "_normal")
        ust = sabit_deger(ust_kod + "_normal")
    if nrt <= 800:
        return round(nrt * taban, 2)
    else:
        return round(800 * taban + (nrt - 800) * ust, 2)

def hesapla_tahlisiye_ucreti(nrt: float, tarife: str, ugraksiz: bool) -> float:
    kod = f"tahlisiye_{tarife}_ugraksiz" if ugraksiz else f"tahlisiye_{tarife}_normal"
    birim = sabit_deger(kod)
    return round(nrt * birim, 2)

def hesapla_kilavuzluk(grt: int, hizmet_turu: str) -> float:
    row = kilavuzluk_df[kilavuzluk_df["hizmet_turu"] == hizmet_turu]
    if row.empty:
        return 0.0
    taban = float(row["taban"].values[0])
    ilave = float(row["ilave"].values[0])
    ek_grt = max(0, grt - 1000)
    ilave_sayi = math.ceil(ek_grt / 1000)
    return round(taban + ilave_sayi * ilave, 2)

def hesapla_acente_ucreti(nrt: int) -> float:
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
        return 640 + math.ceil((nrt - 10000) / 1000) * 30
    elif nrt <= 30000:
        return 640 + (10 * 30) + math.ceil((nrt - 20000) / 1000) * 20
    else:
        return 640 + (10 * 30) + (10 * 20) + math.ceil((nrt - 30000) / 1000) * 10

def hesapla_acente_refakatli(acente_ucreti: float, refakat_var: bool) -> float:
    oran = sabit_deger("refakat_orani") / 100
    return round(acente_ucreti * oran, 2) if refakat_var else 0.0

def hesapla_romorkor(boy: float, cins: str, bogaz: str) -> float:
    df = romorkor_ist_df if bogaz.lower() == "istanbul" else romorkor_can_df
    for _, row in df.iterrows():
        if row["alt_boy"] <= boy <= row["ust_boy"] and row["cins"].strip().lower() == cins.strip().lower():
            return float(row["ucret"])
    return 0.0

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
    romorkor = hesapla_romorkor(boy, cins, bogaz)

    st.subheader("Hesaplama Sonuçları (USD):")
    st.write(f"Sağlık Resmi: {saglik} USD")
    st.write(f"Fener Ücreti: {fener} USD")
    st.write(f"Tahlisiye Ücreti: {tahlisiye} USD")
    st.write(f"Kılavuzluk Ücreti: {kilavuz} USD")
    st.write(f"Acentelik Ücreti: {acente} USD")
    st.write(f"Refakatli Geçiş Ek Acentelik Ücreti: {acente_refakat_usd} USD")
    st.write(f"Römorkör Ücreti ({bogaz.title()} Boğazı, {cins}, {boy} m): {romorkor} USD")

