import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(
    page_title="Dashboard Parkings Nantes",
    page_icon="🅿️",
    layout="wide"
)

@st.cache_data
def load_data():
    """Charge et prépare les données des parkings"""
    df = pd.read_csv('df_finale.csv')   
    return df

@st.cache_data
def load_geojson():
    """Charge les données GeoJSON des communes"""
    with open('244400404_communes-nantes-metropole.geojson', 'r') as f:  
        return json.load(f)

def tracer_map_commune(df, geojson_data,années = None,mois = None,types_parking=None ):

  df_temp = df.copy()
  if années and len(années) > 0:
    df_temp = df_temp[df_temp['year'].isin(années)]
  if mois:
    df_temp = df_temp[df_temp['month'].isin(mois)]

  if types_parking and len(types_parking) > 0:
        df_temp = df_temp[df_temp['type_parking'].isin(types_parking)]

  if df_temp.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return None

  fig = px.choropleth_map(df.groupby(['commune'])['taux_remplissage'].mean().reset_index(), geojson= geojson_data ,color="taux_remplissage",
                            locations="commune", featureidkey="properties.nom",
                            center={"lat": 47.221706, "lon":-1.639484},
                            map_style="carto-positron", zoom=10,color_continuous_scale="plasma"
                            )
  fig.update_layout(
    title=f"Taux de remplissage moyen des parkings par commune ({', '.join(map(str, années))} - Mois {', '.join(map(str, mois))})",
    title_font_size=16
    )
  return fig

def tracer_statistiques(df, parking=None, mois=None, annee=None):
  
    if parking:
        df = df[df['nom_parking'] == parking]
    if mois:
        df = df[df['month'] == mois]
    if annee:
        df = df[df['year'] == annee]

    if df.empty:
        print("Aucune donnée disponible pour ces filtres.")
        return None
    df['day_name'] = pd.Categorical(df['day_name'], categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], ordered=True)

    fig = px.bar(data_frame=df.groupby(['day_name','hour'])['taux_remplissage'].mean().reset_index(), x='hour', y='taux_remplissage',barmode='group',
facet_col='day_name',color='taux_remplissage',color_continuous_scale=['green', 'orange', 'red'],range_y=[0,1])

    fig.update_layout(
    title=f"Statistiques de remplissage des parkings {parking} par heure et par jour",
    yaxis_title="Taux de remplissage moyen (%)",
    coloraxis_colorbar=dict(title="Taux de remplissage"),
    showlegend=False,
    font=dict(size=12))

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])) 
    fig.update_layout(
    margin=dict(t=50, b=50, l=50, r=50),
    height=500) 
    return fig

def appliquer_filtres(df, années=None, mois=None, types_parking=None):
   
        df_filtered = df.copy()
        
        if années and len(années) > 0:
            df_filtered = df_filtered[df_filtered['year'].isin(années)]
        if mois and len(mois) > 0:
            df_filtered = df_filtered[df_filtered['month'].isin(mois)]
        if types_parking and len(types_parking) > 0:
            df_filtered = df_filtered[df_filtered['type_parking'].isin(types_parking)]
        
        return df_filtered



df_finale = load_data()
geojson_data = load_geojson()


st.sidebar.title("Filtres")

# Filtres pour la carte des communes
st.sidebar.subheader("Filtres carte des communes")
années_disponibles = sorted(df_finale['year'].unique())
mois_disponibles = sorted(df_finale['month'].unique())
types_parking_disponibles = sorted(df_finale['type_parking'].unique())

années_selectionnées = st.sidebar.multiselect(
    "Sélectionner les années",
    années_disponibles,
    default=années_disponibles[-1]
)

mois_selectionnés = st.sidebar.multiselect(
    "Sélectionner les mois",
    mois_disponibles,
    default=mois_disponibles
)

types_parking_selectionnés = st.sidebar.multiselect(
    "Types de parking",
    types_parking_disponibles,
    default=types_parking_disponibles
)


df_filtered = appliquer_filtres(
    df_finale,
    années_selectionnées,
    mois_selectionnés,
    types_parking_selectionnés
)


st.title("Dashboard des Parkings Nantes Métropole")

# Première ligne : Carte des communes
st.subheader("Taux de remplissage par commune")
fig_communes = tracer_map_commune(
    df_filtered, 
    geojson_data,
    années_selectionnées,
    mois_selectionnés,
    types_parking_selectionnés
)
st.plotly_chart(fig_communes, use_container_width=True)

# Deuxième ligne : carte des parkings

st.subheader("Cartographie des parkings")
df_map = df_filtered[df_filtered['hour'].isin(range(6, 23))]
#df_map = df_finale[df_finale['hour'].isin(range(6, 23))]
if années_selectionnées and len(années_selectionnées) > 0:
    df_map = df_map[df_map['year'].isin(années_selectionnées)]
if mois_selectionnés and len(mois_selectionnés) > 0:
    df_map = df_map[df_map['month'].isin(mois_selectionnés)]
if types_parking_selectionnés and len(types_parking_selectionnés) > 0:
    df_map = df_map[df_map['type_parking'].isin(types_parking_selectionnés)]

fig_map = px.scatter_map(
    df_map.groupby(['nom_parking', "location.lat", "location.lon", "capacite_voiture", "type_parking"])['taux_remplissage'].mean().reset_index(),
    lat="location.lat",
    lon="location.lon",
    color="taux_remplissage",
    size="capacite_voiture",
    zoom=10,
    size_max=30,
    map_style="carto-positron",
    hover_name='nom_parking',
    text='type_parking',
    color_continuous_scale="plasma",
    labels={'taux_remplissage': 'Taux de remplissage',
            'capacite_voiture': 'Capacité',
            'type_parking': 'Type de parking'}
)

fig_map.update_layout(
    title=f"Cartographie des taux de remplissage ({', '.join(map(str, années_selectionnées))} - Mois {', '.join(map(str, mois_selectionnés))})",
    margin={"r":0,"t":30,"l":0,"b":0}
)
st.plotly_chart(fig_map, use_container_width=True)



## Filtres pour les statistiques détaillées (sous la carte)

st.subheader("Statistiques de remplissage par parking")

col1, col2, col3 , col4 = st.columns(4)   
with col1:
    type_parking_stat = st.selectbox(
        "Type de parking",
        ['P', 'R'],
        format_func=lambda x: "Public" if x == 'P' else "Relais"
    )

with col2:
    # Filtrer les parkings selon le type sélectionné
    parkings_filtrés = sorted(df_finale[df_finale['type_parking'] == type_parking_stat]['nom_parking'].unique())
    parking_selectionné = st.selectbox(
        "Sélectionner un parking",
        parkings_filtrés
    )

with col3:
    mois_stat = st.selectbox(
        "Mois",
        mois_disponibles
    )
with col4 :
    année_stat = st.selectbox(
        "Sélectionner une année",
        années_disponibles
    )


fig_stats = tracer_statistiques(
    df_finale,
    parking_selectionné,
    mois_stat,
    année_stat)
st.plotly_chart(fig_stats, use_container_width=True)

st.markdown("""
### À propos
Ce dashboard présente les données des parkings publics et relais de Nantes Métropole.
- La première carte montre le taux de remplissage moyen par commune
- Le graphique central détaille l'occupation par jour et par heure pour un parking spécifique
- La carte de droite présente tous les parkings avec leur capacité et taux de remplissage
""")