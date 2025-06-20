import streamlit as st
import pydeck as pdk
import pandas as pd
import json


# Title for the app
st.title("Connectivity in Benue and Taraba States")

st.logo('https://static.wixstatic.com/media/8f90d6_882dbd58c7884c1ea5ad885d809f03ac~mv2.png/v1/fill/w_479,h_182,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Notify%20Health%20Logo%20Blue.png',link="https://www.notifyhealth.org/",icon_image='https://static.wixstatic.com/media/8f90d6_882dbd58c7884c1ea5ad885d809f03ac~mv2.png/v1/fill/w_479,h_182,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Notify%20Health%20Logo%20Blue.png')


###### LOAD DATA ######

# Load data for benue health centers
csv_benue = "BENUE-PRIMARY HEALTH CENTERS-data - BENUE-PRIMARY HEALTH CENTERS-data.csv"
df_benue_health_centers = pd.read_csv(csv_benue)
# Filter operational health centers
benue_operational_health_centers = df_benue_health_centers[df_benue_health_centers["is_operational"] == True]

# Load data for taraba health centers
csv_taraba = "TARABA-PRIMARY HEALTH CENTERS-data - TARABA-PRIMARY HEALTH CENTERS-data.csv"
df_taraba_health_centers = pd.read_csv(csv_taraba)
# Filter operational health centers
taraba_operational_health_centers = df_taraba_health_centers[df_taraba_health_centers["is_operational"] == True]

# @st.cache_data
# def load_data(url):
#     return pd.read_csv(url)

# Load data for population 

##### Benue LGA population projections (2025) ##### 
data_population_benue = {
    "Local Government Area": [
        "Ado", "Agatu", "Apa", "Buruku", "Gboko", "Guma", "Gwer East", "GwerWest",
        "Katsina (Benue)", "Konshish", "Kwande", "Logo", "Makurdi", "Obi", "Ogbadibo",
        "Ohimini", "Oju", "Okpokwu", "Oturkpo", "Tarka", "Ukum", "Ushongo", "Vandeiky"
    ],
    "Total Population": [
        286476, 179743, 150425, 320562, 561818, 301785, 262273, 190366, 351086, 352682,
        387228, 264252, 467431, 153523, 203851, 110141, 262058, 272936, 414489, 123429,
        337512, 298528, 365932
    ]
}

# Age group percentages
age_group_percentages = {
    "0–14": 0.392,
    "15–24": 0.181,
    "25–54": 0.332,
    "55+": 0.094
}

# Convert to DataFrame
df_population_benue = pd.DataFrame(data_population_benue)

# Calculate age group populations
for group, pct in age_group_percentages.items():
    df_population_benue[group] = (df_population_benue["Total Population"] * pct).round(0).astype(int)


##### Taraba LGA population projections (2025) ##### 
data_population_taraba = {
    "Local Government Area": [
        "Ardo-Kola", "Bali", "Disputed Areas", "Donga", "Gashaka", "Gassol", "Ibi",
        "Jalingo", "Karim-La", "Kurmi", "Lau", "Sardauna", "Takum", "Ussa", "Wukari", "Yorro", "Zing"
    ],
    "Total Population": [
        150400, 361600, 34200, 228000, 149300, 419600, 144300,
        240300, 332200, 156300, 162900, 384000, 230300, 155800, 406900, 154100, 218600
    ]
}

# Age group percentages (updated)
age_group_percentages_taraba = {
    "0–14": 0.417,
    "15–64": 0.549,
    "65+": 0.033
}

# Convert to DataFrame
df_population_taraba = pd.DataFrame(data_population_taraba)

# Calculate age group populations
for group, pct in age_group_percentages_taraba.items():
    df_population_taraba[group] = (df_population_taraba["Total Population"] * pct).round(0).astype(int)

# Load your GeoJSON
# with open("nigeria_Local_Government_Area_level_2.geojson") as f:
#     geojson_data = json.load(f)

# Find maximum population in your data for scaling
max_population = max(
    df_population_benue["Total Population"].max(), 
    df_population_taraba["Total Population"].max()
)

# Load your GeoJSON
with open("nigeria_lga.geojson") as f:
    geojson_data = json.load(f)

# Map population values to features only for Benue, Kogi, Taraba
for feature in geojson_data["features"]:
    state_name = feature["properties"]["state"]
    lga_name = feature["properties"]["lga"]
    
    # Filter to only the desired states
    # Only work with Benue, Kogi, Taraba
    if state_name in ["Benue", "Kogi", "Taraba"]:
        population = 0
        age_0_14 = 0

        # Check Benue
        match_benue = df_population_benue[df_population_benue["Local Government Area"] == lga_name]
        if not match_benue.empty:
            population = int(match_benue["Total Population"].values[0])
            age_0_14 = int(match_benue["0–14"].values[0])

        # Check Taraba if no Benue match
        match_taraba = df_population_taraba[df_population_taraba["Local Government Area"] == lga_name]
        if not match_taraba.empty:
            population = int(match_taraba["Total Population"].values[0])
            age_0_14 = int(match_taraba["0–14"].values[0])

        feature["properties"]["population"] = population
        feature["properties"]["age_0_14"] = age_0_14
        feature["properties"]["population_str"] = "{:,}".format(population)
        feature["properties"]["age_0_14_str"] = "{:,}".format(age_0_14) 

        green_intensity = max(0, 255 - int((population / max_population) * 255))
        feature["properties"]["color"] = [255, green_intensity, 100, 160]

    else:
        feature["properties"]["population"] = 0
        feature["properties"]["age_0_14"] = 0
        feature["properties"]["color"] = [200, 200, 200, 50]


# Load states GeoJSON
with open("nigeria-states.geojson") as f:
    states_geojson_data = json.load(f)


###### MAP ######

# Create GeoJsonLayer for the choropleth
# geojson_layer = pdk.Layer(
#     "GeoJsonLayer",
#     data=geojson_data,  # <- This should be a Python dict or a URL string
#     stroked=True,
#     filled=False,
#     # get_fill_color="properties.color",
#     get_line_color=[80, 80, 80],
#     lineWidthMinPixels=1.5,   # Add this line
#     pickable=True,
#     auto_highlight=True
# )

geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_data,
    stroked=True,
    filled=True,  # now fill the polygons
    get_fill_color="properties.color",  # now reading your precomputed color    
    get_line_color=[80, 80, 80],
    lineWidthMinPixels=0.6,
    pickable=True,
    auto_highlight=True
)

states_layer = pdk.Layer(
    "GeoJsonLayer",
    data=states_geojson_data,
    stroked=True,
    filled=False,  # transparent fill
    get_line_color=[0, 0, 0, 200],  # black border
    lineWidthMinPixels=2
)

# Create ScatterplotLayer for the Operational Health Centers in Benue
benue_health_centers_layer = pdk.Layer(
    "ScatterplotLayer",
    data=benue_operational_health_centers,  # <- This should be a Python dict or a URL string
    get_position='[longitude, latitude]',
    stroked=False,
    filled=True,
    get_fill_color="[255, 0, 0,160]",  # Or "color" if your DataFrame has a color column
    get_radius=700,
    pickable=True,
    auto_highlight=True
)

# Create ScatterplotLayer for the Operational Health Centers in Taraba
taraba_health_centers_layer = pdk.Layer(
    "ScatterplotLayer",
    data=taraba_operational_health_centers,  # <- This should be a Python dict or a URL string
    get_position='[longitude, latitude]',
    stroked=False,
    filled=True,
    get_fill_color="[0, 0, 255, 160]",  # Or "color" if your DataFrame has a color column
    get_radius=700,
    pickable=True,
    auto_highlight=True
)

# View settings
initial_view_state = pdk.ViewState(
    latitude=7.8,
    longitude=8.45,
    zoom=6,
    pitch=0
)

# Render the map
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=initial_view_state,
    layers=[geojson_layer, benue_health_centers_layer, taraba_health_centers_layer, states_layer],
    # use_container_width=True,
    tooltip = {
    "html": """
        <b>State:</b> {state}<br/>
        <b>LGA:</b> {lga}<br/>
        <b>Est. Total Population:</b> {population_str}<br/>
        <b>Est. Population 0–14:</b> {age_0_14_str}
    """,
    "style": {
        "backgroundColor": "steelblue",
        "color": "white"
    }
}
))

###### SHOW DATA ######
# Checkbox to show data samples
# if st.checkbox("Show sample data Population per Local Government Area (LGA)"):
#     st.write(operational_health_centers.head())

if st.checkbox("Show sample Operational Health Centers data"):
    st.subheader("Benue State")
    st.dataframe(df_benue_health_centers.head(5))  # 
    st.subheader("Taraba State")
    st.dataframe(df_taraba_health_centers.head(5))  # 
