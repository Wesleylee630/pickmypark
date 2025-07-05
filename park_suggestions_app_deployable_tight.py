
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import tempfile

plt.rcParams['font.family'] = 'Arial Unicode MS'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="Park Suggestion Map", layout="wide")

# ---- Static CSS to suppress iframe bottom whitespace ----
st.markdown("""
    <style>
        iframe {
            margin-bottom: -60px !important;
        }
        .element-container:has(iframe) {
            margin-bottom: -60px !important;
        }
    </style>
""", unsafe_allow_html=True)

LANGUAGES = {
    "English": {
        "title": "Park Suggestion Interactive Map",
        "filter_header": "Filter Options",
        "category": "Suggestion Type",
        "age": "Age Group",
        "gender": "Gender",
        "relationship": "User Relationship",
        "map": "Map",
        "export": "Export Charts to PDF",
        "export_btn": "Download PDF",
        "result_header": "Suggestions Found",
        "no_result": "No suggestions found. Adjust filters to see data.",
        "charts": {
            "age": "Age Distribution",
            "gender": "Gender Distribution",
            "category": "Suggestion Type Distribution",
            "relationship": "User Relationship Distribution"
        }
    }
}

TXT = LANGUAGES['English']

st.markdown(f"<h1 style='text-align: center; color: #2C6E49; margin-bottom: 0;'>{TXT['title']}</h1>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 0;'>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("map_survey-5611-submissions-export.xlsx", skiprows=6)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Q1. Category": "Category",
        "Q2. Coordinates": "Coordinates",
        "Q5. Select your age group": "Age",
        "Q6. Select your gender": "Gender",
        "Q8. What is your relationship to the land you want transformed into a new park?": "Relationship",
        "Q13. Is there anything else you’d like to tell us about your idea?": "Comment"
    })
    df = df.dropna(subset=["Coordinates"])
    df[["Latitude", "Longitude"]] = df["Coordinates"].str.split(",", expand=True).astype(float)
    return df

df = load_data()

st.sidebar.header(TXT["filter_header"])

def dropdown_filter(label, options):
    options = sorted(options)
    selected = st.sidebar.multiselect(label, options, default=options)
    return selected

categories = dropdown_filter(TXT["category"], df["Category"].dropna().unique())
ages = dropdown_filter(TXT["age"], df["Age"].dropna().unique())
genders = dropdown_filter(TXT["gender"], df["Gender"].dropna().unique())
relations = dropdown_filter(TXT["relationship"], df["Relationship"].dropna().unique())

filtered_df = df[
    df["Category"].isin(categories) &
    df["Age"].isin(ages) &
    df["Gender"].isin(genders) &
    df["Relationship"].isin(relations)
]

st.markdown(f"<h3 style='margin: 0.25rem 0; color:#2C6E49;'>{TXT['map']}</h3>", unsafe_allow_html=True)

if not filtered_df.empty:
    map_center = [filtered_df["Latitude"].mean(), filtered_df["Longitude"].mean()]
    m = folium.Map(location=map_center, zoom_start=7)

    for _, row in filtered_df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=row["Comment"] if pd.notna(row["Comment"]) else "No comment",
            tooltip=row["Category"],
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, height=500, use_container_width=True)
else:
    st.warning(TXT["no_result"])

def plot_bar_with_labels(data, title, xlabel):
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(data.index, data.values, color="#2C6E49")
    ax.set_title(title, fontsize=13, color="#2C6E49", pad=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ymax = data.max() * 1.05
    ax.set_ylim(0, ymax)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 2), textcoords="offset points", ha='center', fontsize=9)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout(pad=0.1)
    return fig

def export_pdf(category_fig, age_fig, gender_fig, relationship_fig):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    chart_h = (height - 3 * margin) / 2
    charts = [category_fig, age_fig, gender_fig, relationship_fig]
    for i in range(0, len(charts), 2):
        for j in range(2):
            if i + j < len(charts):
                fig = charts[i + j]
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                    fig.savefig(tmpfile.name, format='png', bbox_inches='tight', dpi=150)
                    img = ImageReader(tmpfile.name)
                    y = height - margin - j * (chart_h + margin)
                    c.drawImage(img, margin, y - chart_h, width=width - 2 * margin, height=chart_h, preserveAspectRatio=True)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

if not filtered_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(TXT["charts"]["category"])
        cat_fig = plot_bar_with_labels(filtered_df["Category"].value_counts(), TXT["charts"]["category"], TXT["category"])
        st.pyplot(cat_fig)
    with col2:
        st.markdown(TXT["charts"]["age"])
        age_fig = plot_bar_with_labels(filtered_df["Age"].value_counts().sort_index(), TXT["charts"]["age"], TXT["age"])
        st.pyplot(age_fig)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(TXT["charts"]["gender"])
        gender_counts = filtered_df["Gender"].value_counts()
        fig1, ax1 = plt.subplots()
        wedges, texts, autotexts = ax1.pie(gender_counts, labels=gender_counts.index, autopct="%1.1f%%", startangle=90)
        for text in texts + autotexts:
            text.set_fontsize(10)
        ax1.axis("equal")
        ax1.set_title(TXT["charts"]["gender"], fontsize=13, color="#2C6E49", pad=10)
        st.pyplot(fig1)
    with col4:
        st.markdown(TXT["charts"]["relationship"])
        rel_fig = plot_bar_with_labels(filtered_df["Relationship"].value_counts(), TXT["charts"]["relationship"], TXT["relationship"])
        st.pyplot(rel_fig)

    if st.button(TXT["export"]):
        pdf_buffer = export_pdf(cat_fig, age_fig, fig1, rel_fig)
        st.download_button(
            label=TXT["export_btn"],
            data=pdf_buffer,
            file_name="park_suggestions_charts.pdf",
            mime="application/pdf"
        )
