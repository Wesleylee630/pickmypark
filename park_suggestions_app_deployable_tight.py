
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import tempfile
import leafmap.foliumap as leafmap
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# 多语言配置
LANGUAGES = {
    "English": {
        "title": "Park Suggestions Interactive Map",
        "filter_header": "Filter Options",
        "category": "Suggestion Type",
        "age": "Age Group",
        "gender": "Gender",
        "relationship": "User Relationship",
        "map": "Map",
        "export": "Export Charts to PDF",
        "export_btn": "Download PDF",
        "charts": {
            "age": "Age Distribution",
            "gender": "Gender Distribution",
            "category": "Suggestion Type Distribution",
            "relationship": "User Relationship Distribution"
        }
    }
}

TXT = LANGUAGES["English"]

st.title(TXT["title"])

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

# 筛选器
st.sidebar.header(TXT["filter_header"])
categories = st.sidebar.multiselect(TXT["category"], df["Category"].dropna().unique(), default=df["Category"].dropna().unique())
ages = st.sidebar.multiselect(TXT["age"], df["Age"].dropna().unique(), default=df["Age"].dropna().unique())
genders = st.sidebar.multiselect(TXT["gender"], df["Gender"].dropna().unique(), default=df["Gender"].dropna().unique())
relations = st.sidebar.multiselect(TXT["relationship"], df["Relationship"].dropna().unique(), default=df["Relationship"].dropna().unique())

filtered_df = df[
    df["Category"].isin(categories) &
    df["Age"].isin(ages) &
    df["Gender"].isin(genders) &
    df["Relationship"].isin(relations)
]

# 显示地图
st.subheader(TXT["map"])
if not filtered_df.empty:
    m = leafmap.Map(center=[filtered_df["Latitude"].mean(), filtered_df["Longitude"].mean()], zoom=7)
    for _, row in filtered_df.iterrows():
        popup = row["Comment"] if pd.notna(row["Comment"]) else "No comment"
        m.add_marker(location=[row["Latitude"], row["Longitude"]], popup=popup)
    components.html(m.to_html(), height=600, scrolling=False)
else:
    st.warning("No suggestions found. Adjust filters to see data.")

# 图表绘制
def plot_bar_with_labels(data, title, xlabel):
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(data.index, data.values, color="#2C6E49")
    ax.set_title(title, fontsize=13, color="#2C6E49", pad=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 2), textcoords="offset points", ha='center', fontsize=9)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return fig

if not filtered_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        cat_fig = plot_bar_with_labels(filtered_df["Category"].value_counts(), TXT["charts"]["category"], TXT["category"])
        st.pyplot(cat_fig)

    with col2:
        age_fig = plot_bar_with_labels(filtered_df["Age"].value_counts().sort_index(), TXT["charts"]["age"], TXT["age"])
        st.pyplot(age_fig)

    col3, col4 = st.columns(2)
    with col3:
        gender_fig = plot_bar_with_labels(filtered_df["Gender"].value_counts(), TXT["charts"]["gender"], TXT["gender"])
        st.pyplot(gender_fig)

    with col4:
        rel_fig = plot_bar_with_labels(filtered_df["Relationship"].value_counts(), TXT["charts"]["relationship"], TXT["relationship"])
        st.pyplot(rel_fig)

    def export_pdf(*figures):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 40
        chart_h = (height - 3 * margin) / 2
        for i in range(0, len(figures), 2):
            for j in range(2):
                if i + j < len(figures):
                    fig = figures[i + j]
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                        fig.savefig(tmpfile.name, format='png', bbox_inches='tight', dpi=150)
                        img = ImageReader(tmpfile.name)
                        y = height - margin - j * (chart_h + margin)
                        c.drawImage(img, margin, y - chart_h, width=width - 2 * margin, height=chart_h, preserveAspectRatio=True)
            c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    if st.button(TXT["export"]):
        pdf_buf = export_pdf(cat_fig, age_fig, gender_fig, rel_fig)
        st.download_button(TXT["export_btn"], data=pdf_buf, file_name="charts.pdf", mime="application/pdf")
