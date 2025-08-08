
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

def sabit_deger(kalem_adi):
    row = sabitler_df[sabitler_df["kalem"] == kalem_adi]
    return float(row["deger"].values[0]) if not row.empty else 0.0

def hesapla_saglik_resmi(nrt: float, usd_try_kur: float) -> float:
    katsayi = sabit_deger("saglik_katsayi")
    return round(katsayi * usd_try_kur * nrt, 2)

def hesapla_fener_ucreti(nrt: float) -> float:
    ilk_oran = sabit_deger("fener_ilk_800_nt")
    ust_oran = sabit_deger("fener_800_ustu_nt")
    if nrt <= 800:
        return round(nrt * ilk_oran, 2)
    else:
        return round((800 * ilk_oran) + ((nrt - 800) * ust_oran), 2)

def hesapla_tahlisiye_ucreti(nrt: float) -> float:
    birim = sabit_deger("tahlisiye_birim")
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

# Streamlit Arayüzü
st.title("Boğaz Geçişi Proforma Hesaplama")

nrt = st.number_input("NRT (Net Register Tonnage)", value=1500)
grt = st.number_input("GRT (Gross Register Tonnage)", value=2500)
boy = st.number_input("Gemi Boyu (metre)", value=180.0)
cins = st.selectbox("Gemi Cinsi", ["TANKER", "LPG", "NÜKLEER", "TANKER/LPG", "LPG/ NÜKLEER", "RO-RO/KONT /DİGER"])
bogaz = st.selectbox("Boğaz", ["istanbul", "çanakkale"])
usd_try_kur = st.number_input("USD/TRY kuru", value=32.5)
refakat_var = st.checkbox("Refakatli geçiş mi?", value=True)

if st.button("Hesapla"):
    saglik = hesapla_saglik_resmi(nrt, usd_try_kur)
    fener = hesapla_fener_ucreti(nrt)
    tahlisiye = hesapla_tahlisiye_ucreti(nrt)
    kilavuz = hesapla_kilavuzluk(grt, "bogaz_gecisi")
    acente = hesapla_acente_ucreti(nrt)
    acente_refakat = hesapla_acente_refakatli(acente, refakat_var)
    romorkor = hesapla_romorkor(boy, cins, bogaz)

    st.subheader("Hesaplama Sonuçları:")
    st.write(f"Sağlık Resmi (TRY): {saglik}")
    st.write(f"Fener Ücreti (USD): {fener}")
    st.write(f"Tahlisiye Ücreti (USD): {tahlisiye}")
    st.write(f"Kılavuzluk Ücreti (USD): {kilavuz}")
    st.write(f"Acentelik Ücreti (EUR): {acente}")
    st.write(f"Refakatli Geçiş Ek Acentelik Ücreti (EUR): {acente_refakat}")
    st.write(f"Römorkör Ücreti ({bogaz.title()} Boğazı, {cins}, {boy} m): {romorkor} USD")
