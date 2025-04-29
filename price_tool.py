import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime
from PIL import Image

# Stel de pagina-configuratie in
st.set_page_config(
    page_title="GHX Price Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Controleer of logo bestand bestaat, zo niet, gebruik een placeholder tekst
try:
    logo = Image.open('ghx_logo.png')
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(logo, width=300)  # Logo grootte verdubbeld naar 300
    with col2:
        st.title("Price Tool")  # Titel gewijzigd naar alleen Price Tool
except:
    st.title("Price Tool")

# Beschrijving onder de titel
st.markdown("Een tool voor het berekenen van optimale prijzen en het verwerken van data.")

# CSS styling voor een modernere interface
st.markdown("""
<style>
    /* GHX Kleurenschema - Pas deze aan naar de huisstijl van GHX */
    :root {
        --ghx-primary: #005EB8;      /* Primaire kleur - Blauw */
        --ghx-secondary: #00A651;    /* Secundaire kleur - Groen */
        --ghx-accent: #F7941D;       /* Accent kleur - Oranje */
        --ghx-light: #E8F1F8;        /* Licht blauw voor achtergronden */
        --ghx-dark: #1A1A1A;         /* Donkere tekst kleur */
        --ghx-background: #FFFFFF;   /* Achtergrondkleur */
    }
    
    /* Algemene stijlen */
    .main {
        background-color: var(--ghx-light);
    }
    h1, h2, h3 {
        color: var(--ghx-primary);
    }
    
    /* Tab stijlen */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--ghx-background);
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--ghx-primary);
        color: white;
    }
    
    /* Componenten */
    .st-bw {
        background-color: var(--ghx-background);
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Knoppen */
    .stButton button {
        background-color: var(--ghx-primary);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
    }
    .stButton button:hover {
        background-color: #00479B;  /* Donkerdere versie van primaire kleur */
    }
    
    /* Metrics en andere elementen */
    .css-1l40rdr, .css-1aehpvj {
        color: var(--ghx-primary);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--ghx-light);
        border-radius: 5px;
    }
    
    /* Logo stijl */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .logo-image {
        margin-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Functies voor prijsberekeningen
def calculate_costs(orders, small_start_cost, small_start_orders, 
                   big_start_cost, big_start_orders,
                   small_prepaid_cost, small_prepaid_orders,
                   big_prepaid_cost, big_prepaid_orders,
                   overage_cost):
    """Berekent de optimale kosten voor een gegeven aantal orders"""
    # Bepaal welke startbundel te gebruiken
    if small_start_orders >= orders:
        # Small bundel is voldoende
        return small_start_cost, "Small Start"
    elif big_start_orders >= orders:
        # Kies de goedkoopste optie tussen small+prepaid of big start
        small_with_prepaids_needed = (orders - small_start_orders) // small_prepaid_orders
        if orders - small_start_orders > small_with_prepaids_needed * small_prepaid_orders:
            small_with_prepaids_needed += 1
        
        small_total_cost = small_start_cost + small_with_prepaids_needed * small_prepaid_cost
        
        if small_total_cost < big_start_cost:
            return small_total_cost, "Small Start + Prepaids"
        else:
            return big_start_cost, "Big Start"
    else:
        # Complexere situatie met grote orders
        # Optie 1: Small start met prepaids
        remaining_after_small = orders - small_start_orders
        small_prepaids_needed = remaining_after_small // small_prepaid_orders
        if remaining_after_small % small_prepaid_orders > 0:
            small_prepaids_needed += 1
        small_total = small_start_cost + small_prepaids_needed * small_prepaid_cost
        
        # Optie 2: Big start met prepaids
        remaining_after_big = orders - big_start_orders
        big_prepaids_needed = remaining_after_big // big_prepaid_orders
        remaining_after_big_prepaids = remaining_after_big - (big_prepaids_needed * big_prepaid_orders)
        
        # Als er nog orders overblijven, bereken overage kosten
        overage_costs = 0
        if remaining_after_big_prepaids > 0:
            overage_costs = remaining_after_big_prepaids * overage_cost
        
        big_total = big_start_cost + big_prepaids_needed * big_prepaid_cost + overage_costs
        
        # Return goedkoopste optie
        if small_total < big_total:
            return small_total, "Small Start + Prepaids"
        else:
            return big_total, "Big Start + Prepaids"

def bundle_description(strategy, orders, small_start_orders, big_start_orders, 
                       small_prepaid_orders, big_prepaid_orders):
    """Genereer een gedetailleerde beschrijving van de gekozen strategie"""
    description = f"**{strategy}**\n\n"
    
    if strategy == "Small Start":
        description += f"• 1 Small Start Bundel ({small_start_orders} orders)\n"
    elif strategy == "Big Start":
        description += f"• 1 Big Start Bundel ({big_start_orders} orders)\n"
    elif "Small Start + Prepaids" in strategy:
        # Bereken hoeveel prepaids
        remaining = orders - small_start_orders
        prepaids_needed = remaining // small_prepaid_orders
        if remaining % small_prepaid_orders > 0:
            prepaids_needed += 1
        
        description += f"• 1 Small Start Bundel ({small_start_orders} orders)\n"
        description += f"• {prepaids_needed} Small Prepaid Bundel(s) ({prepaids_needed * small_prepaid_orders} orders)\n"
    elif "Big Start + Prepaids" in strategy:
        # Bereken hoeveel prepaids en eventuele overage
        remaining = orders - big_start_orders
        prepaids_needed = remaining // big_prepaid_orders
        remaining_after_prepaids = remaining - (prepaids_needed * big_prepaid_orders)
        
        description += f"• 1 Big Start Bundel ({big_start_orders} orders)\n"
        if prepaids_needed > 0:
            description += f"• {prepaids_needed} Big Prepaid Bundel(s) ({prepaids_needed * big_prepaid_orders} orders)\n"
        if remaining_after_prepaids > 0:
            description += f"• {remaining_after_prepaids} Overage Orders\n"
    
    description += f"\nTotaal: {orders} orders"
    return description

def display_costs_df(orders, small_start_cost, small_start_orders, 
                    big_start_cost, big_start_orders,
                    small_prepaid_cost, small_prepaid_orders,
                    big_prepaid_cost, big_prepaid_orders,
                    overage_cost):
    """Genereer een DataFrame met kosten voor verschillende strategieën"""
    strategies = []
    
    # Small Start
    if orders <= small_start_orders:
        cost = small_start_cost
        strategies.append({
            'Strategie': 'Small Start',
            'Kosten': cost,
            'Kosten per Order': cost / orders,
            'Bundels': '1 Small Start'
        })
    else:
        # Small Start + Prepaids
        remaining = orders - small_start_orders
        prepaids_needed = remaining // small_prepaid_orders
        if remaining % small_prepaid_orders > 0:
            prepaids_needed += 1
        
        cost = small_start_cost + (prepaids_needed * small_prepaid_cost)
        strategies.append({
            'Strategie': 'Small Start + Prepaids',
            'Kosten': cost,
            'Kosten per Order': cost / orders,
            'Bundels': f'1 Small Start, {prepaids_needed} Small Prepaids'
        })
    
    # Big Start
    if orders <= big_start_orders:
        cost = big_start_cost
        strategies.append({
            'Strategie': 'Big Start',
            'Kosten': cost,
            'Kosten per Order': cost / orders,
            'Bundels': '1 Big Start'
        })
    else:
        # Big Start + Prepaids + Overage
        remaining = orders - big_start_orders
        prepaids_needed = remaining // big_prepaid_orders
        remaining_after_prepaids = remaining - (prepaids_needed * big_prepaid_orders)
        
        cost = big_start_cost + (prepaids_needed * big_prepaid_cost)
        bundels = f'1 Big Start, {prepaids_needed} Big Prepaids'
        
        if remaining_after_prepaids > 0:
            overage_costs = remaining_after_prepaids * overage_cost
            cost += overage_costs
            bundels += f', {remaining_after_prepaids} Overage'
        
        strategies.append({
            'Strategie': 'Big Start + Prepaids + Overage',
            'Kosten': cost,
            'Kosten per Order': cost / orders,
            'Bundels': bundels
        })
    
    # Maak DataFrame en sorteer op kosten
    df = pd.DataFrame(strategies)
    df = df.sort_values('Kosten')
    
    # Formateer kolommen
    df['Kosten'] = df['Kosten'].map('€{:.2f}'.format)
    df['Kosten per Order'] = df['Kosten per Order'].map('€{:.2f}'.format)
    
    return df

# Functies voor het verwerken van data
def process_uploaded_file(uploaded_file):
    """Verwerkt een geüpload Excel of CSV bestand naar een pandas DataFrame"""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    return df

def download_link(df, filename, link_text):
    """Genereer een download link voor een DataFrame als Excel of CSV"""
    if filename.endswith('.csv'):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        b64 = base64.b64encode(output.getvalue()).decode()
        href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
    
    return f'<a href="{href}" download="{filename}">{link_text}</a>'

# Uitleg van de app toevoegen
with st.expander("ℹ️ Over deze app", expanded=False):
    st.markdown("""
    ### GHX Price Tool functionaliteiten
    
    Met de GHX Price Tool kun je:
    - De optimale prijsstrategie berekenen voor een gegeven aantal orders
    - Verschillende bundel-opties vergelijken
    - Kosten per order en totale kosten analyseren
    - Resultaten exporteren voor rapportage
    
    Deze tool helpt je bij het maken van de juiste prijsbeslissingen voor GHX klanten.
    """)

# Prijscalculator interface zonder tabs
st.header("📊 Prijscalculator")

# Prijscalculator functionaliteit
with st.expander("⚙️ Parameters", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Algemeen")
        orders = st.number_input("Aantal Orders", min_value=1, value=5000)
        
        st.subheader("Start Bundels")
        small_start_cost = st.number_input("Small Start Kosten (€)", min_value=0, value=1000)
        small_start_orders = st.number_input("Small Start Orders", min_value=1, value=100)
        
        big_start_cost = st.number_input("Big Start Kosten (€)", min_value=0, value=2000)
        big_start_orders = st.number_input("Big Start Orders", min_value=1, value=1350)
    
    with col2:
        st.subheader("Prepaid Bundels")
        small_prepaid_cost = st.number_input("Small Prepaid Kosten (€)", min_value=0, value=250)
        small_prepaid_orders = st.number_input("Small Prepaid Orders", min_value=1, value=250)
        
        big_prepaid_cost = st.number_input("Big Prepaid Kosten (€)", min_value=0, value=1000)
        big_prepaid_orders = st.number_input("Big Prepaid Orders", min_value=1, value=1100)
        
        st.subheader("Overage")
        overage_cost = st.number_input("Overage Kosten per Order (€)", min_value=0.0, value=2.0, step=0.1)

# Bereken en toon resultaten
if st.button("Berekenen", key="calculate_button", use_container_width=True):
    total_cost, strategy = calculate_costs(
        orders, small_start_cost, small_start_orders, 
        big_start_cost, big_start_orders,
        small_prepaid_cost, small_prepaid_orders,
        big_prepaid_cost, big_prepaid_orders,
        overage_cost
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Optimale Strategie")
        st.markdown(bundle_description(
            strategy, orders, small_start_orders, big_start_orders,
            small_prepaid_orders, big_prepaid_orders
        ), unsafe_allow_html=True)
    
    with col2:
        st.subheader("Kostenoverzicht")
        st.metric("Totale Kosten", f"€{total_cost:.2f}")
        st.metric("Kosten per Order", f"€{total_cost/orders:.2f}")
    
    st.subheader("Vergelijking van Strategieën")
    costs_df = display_costs_df(
        orders, small_start_cost, small_start_orders, 
        big_start_cost, big_start_orders,
        small_prepaid_cost, small_prepaid_orders,
        big_prepaid_cost, big_prepaid_orders,
        overage_cost
    )
    st.dataframe(costs_df, use_container_width=True)
    
    # Download optie - oplossing voor Excel error
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        costs_df.to_excel(writer, index=False)
    buffer.seek(0)
    
    st.download_button(
        label="Download Resultaten als Excel",
        data=buffer,
        file_name=f"prijsberekening_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.ms-excel"
    )

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<div style='text-align: center; color: #666;'>GHX Price Tool | © Global Healthcare Exchange, LLC</div>", unsafe_allow_html=True)
