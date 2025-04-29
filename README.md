# GHX Pricing Tool

Een interactieve Streamlit-applicatie voor het berekenen van optimale prijsbundels voor verschillende orderaantallen.

## Functionaliteiten

- **Prijsmodel Calculator**: Bereken optimale bundel combinaties voor gegeven orderaantallen
- **Data Upload & Bewerking**: Upload Excel bestanden, filter en sorteer data, en selecteer relevante kolommen
- **Data Export**: Download berekeningen en bewerkte data als Excel bestanden
- **Kostenvergelijking**: Visualiseer kostentrends over verschillende orderaantallen
- **Authenticatie**: Beveiligde toegang met gebruikersnaam en wachtwoord

## Installatie en gebruik (lokaal)

### Vereisten

- Python 3.8+
- pip

### Installatie

1. Clone dit repository:
   ```
   git clone <repository_url>
   cd GHX_pricetool
   ```

2. Installeer de benodigde packages:
   ```
   pip install -r requirements.txt
   ```

3. Start de applicatie:
   ```
   # Voor basisversie zonder login
   streamlit run app.py
   
   # Voor versie met login
   streamlit run app_met_login.py
   ```

4. Open de webbrowser en ga naar:
   ```
   http://localhost:8501
   ```

### Login gegevens (voor versie met login)

- Gebruikersnaam: `admin`, Wachtwoord: `admin`
- Gebruikersnaam: `gebruiker`, Wachtwoord: `password`

## Deployment met Docker

### Vereisten

- Docker
- Docker Compose

### Installatie en deployment

1. Build en start de container:
   ```
   docker-compose up -d
   ```

2. Open de webbrowser en ga naar:
   ```
   http://localhost:8501
   ```

3. Om de container te stoppen:
   ```
   docker-compose down
   ```

## Gebruik

### Prijsmodel Calculator

1. Voer het aantal orders in
2. Configureer de bundel parameters (kosten en aantal orders)
3. Bekijk de resultaten in de tabel en grafiek
4. Download de resultaten als Excel bestand

### Data Upload & Bewerking

1. Upload een Excel of CSV bestand
2. Selecteer de kolommen die je wilt weergeven
3. Sorteer en filter de data naar behoefte
4. Download de gefilterde data als Excel bestand

### Kostenvergelijking

1. Stel het bereik van orderaantallen in
2. Klik op "Genereer Vergelijking"
3. Bekijk de grafiek en data
4. Download de vergelijkingsdata als Excel bestand
