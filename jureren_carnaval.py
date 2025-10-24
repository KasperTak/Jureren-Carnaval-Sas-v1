import numpy as np
import math
import pandas as pd
import openpyxl
import streamlit as st
import pandas as pd
import altair as alt
import base64
import io
from PIL import Image
import json
import os
import glob
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
st.set_page_config(page_title="Jureren Betekoppen")
#%%
# INITIALISATIE VAN STATE
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

#%% GOOGLES SHEETS SETUP

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open de Google Sheet
sheet = client.open("Jury_beoordelingen_2026_v1").worksheet("Beoordeling")


#%%
USERS = {
    'admin': 'admin',
    'jury_w1': "wachtwoord_w1",
    'jury_w2': "wachtwoord_w2",
    'jury_w3': "wachtwoord_w3",
    'jury_w4': "wachtwoord_w4",
    'jury_w5': "wachtwoord_w5",
    'jury_w6': "wachtwoord_w6",
    'jury_w7': "wachtwoord_w7",
    'jury_w8': "wachtwoord_w8",
    'jury_w9': "wachtwoord_w9",
    'jury_g1': "wachtwoord_g1",
    'jury_g2': "wachtwoord_g2",
    'jury_g3': "wachtwoord_g3",
    'jury_g4': "wachtwoord_g4",
    'jury_g5': "wachtwoord_g5",
    'jury_g6': "wachtwoord_g6",
    'jury_g7': "wachtwoord_g7",
    'jury_g8': "wachtwoord_g8",
    'jury_g9': "wachtwoord_g9",
    }

def login():
    st.title("Jury login")
    
    username = st.text_input("Gebruikersnaam")
    password = st.text_input("Wachtwoord", type='password')
    
    if st.button("Inloggen"):
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state['username'] = username
            st.success(f"Welkom {username}!")
            st.experimental_rerun()
        else:
            st.error("Ongeldig gebruikersnaam of wachtwoord")
            st.write('*Bij hulp: app admin via 06 29927267*')
#%% 
# def get_json_path(jurylid):
#     folder = "data"
#     if not os.path.exists(folder):
#         os.makedirs(folder)
#     return os.path.join(folder, f"{jurylid}.json")

#%%
def beoordeling_categorie_jurylid(categorie, jurylid):
    st.header(f'Beoordeel de stoetlopers van de categorie {categorie}')
    criteria = ['Idee', 'Bouwtechnisch', 'Afwerking', 'Carnavalesk', 'Actie']
    
    # Bestaande beoordelingen ophalen 
    @st.cache_data(ttl=60)
    def load_existing_data():
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    df_existing = load_existing_data()
    
    # Filter programma op categorie
    df_tab = programma_df[programma_df['categorie'].str.contains(categorie, case=False, na=False)]

    for i, row in df_tab.iterrows():
        vereniging = str(row['vereniging']).strip() if pd.notna(row['vereniging']) else "Onbekend"
        titel = str(row['titel']).strip() if pd.notna(row['titel']) else "Zonder titel"
        
        st.divider()
        st.markdown(f"### 🎭 **{titel}** - {vereniging}")
        
        # Controleren op dit jurylid deze deelnemer al heeft beoordeeld
        mask = (
            (df_existing["Jurylid"] == jurylid)
            & (df_existing["Deelnemer_vereniging"] == vereniging)
            & (df_existing["Deelnemer_titel"] == titel)
            )
        
        if not df_existing.empty and mask.any():
            bestaande_rij = df_existing.loc[mask].iloc[0]
            default_scores = [
                bestaande_rij.get("Idee", 5),
                bestaande_rij.get("Bouwtechnisch", 5),
                bestaande_rij.get("Afwerking", 5),
                bestaande_rij.get("Carnavalesk", 5),
                bestaande_rij.get("Actie", 5),
                ]
            st.info("🟡 Bestaande beoordeling gevonden - je kunt aanpassen of bijwerken")
        else:
            default_scores = [5] * len(criteria)
            
            
        # Data tonen met bestaande of standaardwaardes via data_editor
        editor_df = pd.DataFrame({
            "Criterium": criteria,
            "Beoordeling (1-10)": default_scores})
        editor_key = f"data_editor_{i}_{jurylid}"
        editor_df = st.data_editor(
            editor_df,
            key = editor_key,
            num_rows="fixed",
            column_config={
                "Beoordeling (1-10)": st.column_config.NumberColumn(
                            "Beoordeling (1-10)",
                            min_value = 1,
                            max_value = 10,
                            step = 1)
                }
            )
        
        # Opslaan
        btn_key = f"btn_save_{i}_{jurylid}"
        if st.button(f"💾 Opslaan beoordeling ({titel})", key=btn_key):
            try:
                # Dictionary aanmaken van alle scores
                new_row = {
                    "Jurylid": jurylid,
                    "Categorie": categorie,
                    "Deelnemer_vereniging": vereniging,
                    "Deelnemer_titel": titel,
                    "Idee": int(editor_df.loc[editor_df['Criterium']=="Idee", "Beoordeling (1-10)"].values[0]),
                    "Bouwtechnisch": int(editor_df.loc[editor_df['Criterium'] == "Bouwtechnisch", "Beoordeling (1-10)"].values[0]),
                    "Afwerking": int(editor_df.loc[editor_df['Criterium'] == "Afwerking", "Beoordeling (1-10)"].values[0]),
                    "Carnavalesk": int(editor_df.loc[editor_df['Criterium'] == "Carnavalesk", "Beoordeling (1-10)"].values[0]),
                    "Actie": int(editor_df.loc[editor_df['Criterium'] == "Actie", "Beoordeling (1-10)"].values[0]),
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                
                # checken of er moet worden overgeschreven of toevoegen
                if not df_existing.empty and mask.any():
                    row_index = mask[mask].index[0] + 2
                    sheet.update(f"A{row_index}:H{row_index}", [list(new_row.values())])
                    st.info(f"🔁 Beoordeling bijgewerkt voor {titel}")
                else:
                    sheet.append_row(list(new_row.values()))
                    st.success(f"✅ Nieuwe beoordeling opgeslagen voor {titel}")
                    
                    # Cache verversen
                    load_existing_data.clear()
                    load_existing_data()
                    
            except Exception as e:
                    st.error(f"❌ Fout bij opslaan: {e}")
    # ------- 
   
#%% 
if not st.session_state['logged_in']:
    login()

else:
    jurylid = st.session_state["username"]
    st.sidebar.success(f"Ingelogd als: {st.session_state['username']}")

    
    
    st.title("Jury carnavalsoptocht Sas van Gent")
    
    @st.cache_data(ttl=60)
    def load_programma():
        df = pd.read_excel("Programma stoetopstellers 2024.xlsx")
        return df
    programma_df = load_programma()
    programma_df = programma_df.dropna(how='all')
    programma_df = programma_df[programma_df['categorie'].notna() & programma_df['nr..1'].notna()]
    
    
        
    if "soort_jury" not in st.session_state:
        st.session_state.soort_jury = None
    if "jurylid_nummer" not in st.session_state:
        st.session_state.jurylid_nummer = None
        
    tab_labels = ['Home']
    
    if st.session_state.soort_jury == 'Wagens':
        tab_labels += ["Wagens A", "Wagens B", 
                        "Trio's & Kwartetten A", "Trio's & Kwartetten B",
                        "Eenlingen & Duo's A", "Eenlingen & Duo's B", 
                        'Uitslag']
    elif st.session_state.soort_jury == 'Groepen':
        tab_labels += ['Groepen A', 'Groepen B', 'Groepen C', 'Uitslag']
        
    
    # Tabs maken op basis van labels
    tabs = st.tabs(tab_labels)
    jurylid_nummer = None
    # Home-tab
    with tabs[0]:
        st.title("🏠 Homepagina – Jury-instellingen")
        st.title("Welkom jurylid")
        st.write("Vul hieronder je informatie in:")
        
        
        soort_jury = st.radio("Welke categorie wilt u jureren?", ['Wagens', 'Groepen'], 
                              key = 'radio_soort_jury', 
                              # disabled= st.session_state.disabled_choices, 
                              horizontal=True,
                              index=0)
        
        if soort_jury == 'Wagens':
            jurylid_nummer = st.selectbox("Met welk jurylid hebben we te maken?",
                                      ("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9"), index=0) #, disabled= st.session_state.disabled_choices)
            
        elif soort_jury == 'Groepen':
            jurylid_nummer = st.selectbox("Met welk jurylid hebben we te maken?",
                                      ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"), index=0) #, disabled= st.session_state.disabled_choices)
    
        if jurylid_nummer:
                st.write(f"Welkom {jurylid_nummer} voor categorie {soort_jury}!")
                # st.checkbox('Check en doorgaan!', key='disable_radio', value=st.session_state.disabled_choices, on_change=toggle_radio)
                if st.button("Check en doorgaan!"):
                    st.session_state.soort_jury = soort_jury
                    st.session_state.jurylid_nummer = jurylid_nummer
                    st.success(f"Ingelogd als {jurylid_nummer} voor {soort_jury}.")
                    st.experimental_rerun()
                    
       # img = Image.open(r"C:\Users\Gebruiker\OneDrive\Privé\Programmeren\Carnaval Sas Van Gent\betekoppen_logo.png") 
        #st.image(img, use_container_width=True)
      
    
    if st.session_state.soort_jury == 'Wagens':
        with tabs[1]:
            st.write(df_existing.columns.tolist())
            beoordeling_categorie_jurylid("Wagens A", jurylid)
    #------------------------------------------------------------------------------------------------------------------------------------------------
        # kolom/tabblad 2: categorie WAGENS A
        with tabs[2]:
            beoordeling_categorie_jurylid("Wagens B", jurylid)
            
        # kolom/tabblad 7: categorie Trio's & Kwartetten A 
        with tabs[3]:
            beoordeling_categorie_jurylid("TK-A", jurylid)
            
        # kolom/tabblad 8: categorie Trio's & Kwartetten A 
        with tabs[4]:
            beoordeling_categorie_jurylid("TK-B", jurylid)
            
        # kolom/tabblad 9: categorie Eenlingen & Duo's A 
        with tabs[5]:
            beoordeling_categorie_jurylid("ED-A", jurylid)
            
        # kolom/tabblad 10: categorie Eenlingen & Duo's B
        with tabs[6]:
            beoordeling_categorie_jurylid("ED-B", jurylid)
        
        with tabs[7]:
            st.header("Uitslag")
            st.write("Ook nog jouw top-3 deelnemers invullen voor *De leutigste deelnemer*.")
            
    
    elif st.session_state.soort_jury == 'Groepen':
        # kolom/tabblad 4: categorie GROEPEN A    
        with tabs[1]:
            beoordeling_categorie_jurylid('Groepen A', jurylid)   
            
        # kolom/tabblad 5: categorie GROEPEN B
        with tabs[2]:
            beoordeling_categorie_jurylid("Groepen B", jurylid)
            
        # kolom/tabblad 6: categorie GROEPEN C    
        with tabs[3]:
            beoordeling_categorie_jurylid("Groepen C", jurylid)
            
        with tabs[4]:
            st.header("Uitslag")
            st.write("Ook nog jouw top-3 deelnemers invullen voor *De leutigste deelnemer*.")
        
    
    
    # with tab11:
    #     all_data = []
    #     for f in glob.glob("data/*.json"):
    #         with open(f) as file:
    #             data = json.load(file)
    #             all_data.extend(data)
    #     df = pd.DataFrame(all_data)

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        








