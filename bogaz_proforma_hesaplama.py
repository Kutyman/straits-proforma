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

with st.expander("🔧 Gemi Bilgileri ve Parametreler", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        nrt = st.number_input("NRT (Net Register Tonnage)", value=1500)
        grt = st.number_input("GRT (Gross Register Tonnage)", value=2500)
        boy = st.number_input("Gemi Boyu (metre)", value=180.0)

    with col2:
        cins = st.selectbox("Gemi Cinsi", ["TANKER", "LPG", "NÜKLEER", "TANKER/LPG", "LPG/ NÜKLEER", "RO-RO/KONT /DİGER"])
        kalkis = st.text_input("Kalkış Limanı (ülke veya liman adı)", value="Yunanistan")
        varis = st.text_input("Varış Limanı (ülke veya liman adı)", value="Samsun")

    with col3:
        usd_try_kur = st.number_input("USD/TRY kuru", value=32.5)
        eur_usd_kur = st.number_input("EUR/USD kuru", value=1.08)
        refakat_var = st.checkbox("Refakatli geçiş mi?", value=True)
        turk_bayrakli = st.checkbox("Türk bayraklı mı?", value=False)
        kabotaj_mi = st.checkbox("Kabotaj seferi mi?", value=False)
        yolcu_gemisi_mi = st.checkbox("Yolcu gemisi mi?", value=False)

# Uğraksız geçiş mi?
ugraksiz_mi = kalkis != "" and varis != "" and kalkis.lower() != varis.lower() and not turk_bayrakli and not kabotaj_mi

# Boğaz yönü belirleme
bogaz_gecir = []
kalkis_marmara = any(k in kalkis.lower() for k in ["tekirdag", "gemlik", "marmara", "istanbul", "yarimca", "izmit"])
varis_marmara = any(k in varis.lower() for k in ["tekirdag", "gemlik", "marmara", "istanbul", "yarimca", "izmit"])

if kalkis_marmara or varis_marmara:
    if kalkis_marmara and not varis_marmara:
        bogaz_gecir = ["istanbul"]
    elif varis_marmara and not kalkis_marmara:
        bogaz_gecir = ["çanakkale"]
    else:
        bogaz_gecir = []
else:
    bogaz_gecir = ["çanakkale", "istanbul"]

# Tarifeyi belirle
tarife_kodu = "yabanci"
if kabotaj_mi:
    tarife_kodu = "kabotaj"
elif turk_bayrakli:
    tarife_kodu = "turk"
elif yolcu_gemisi_mi:
    tarife_kodu = "yolcu"

# Fonksiyonlar
# (diğer fonksiyonlar aynı kalacak)

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
