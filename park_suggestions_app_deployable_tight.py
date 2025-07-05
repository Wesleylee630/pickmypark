import streamlit_folium
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial Unicode MS'
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(page_title="Park Suggestion Map", layout="wide")

# 仅在 app 完整加载后再触发 rerun，避免初始化时崩溃
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

if st.session_state.refresh_count < 2:
    st.session_state.refresh_count += 1

    # 👇 用 st.stop() 延迟 rerun 执行，等 app 完整加载后再触发 rerun
    st.stop()

# 多语言配置
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
    },
    "中文": {
        "title": "公园建议互动地图",
        "filter_header": "筛选条件",
        "category": "建议类型",
        "age": "年龄段",
        "gender": "性别",
        "relationship": "用户关系",
        "map": "地图",
        "export": "导出图表为 PDF",
        "export_btn": "下载 PDF",
        "result_header": "符合条件的建议数量",
        "no_result": "当前筛选条件下没有任何建议，请调整筛选器以查看数据。",
        "charts": {
            "age": "年龄分布",
            "gender": "性别分布",
            "category": "建议类型分布",
            "relationship": "用户关系类型分布"
        }
    }
}

# 语言选择
# "English" selection removed"Language / 语言", list(LANGUAGES.keys()))
TXT = LANGUAGES['English']

st.markdown(f"<h1 style='text-align: center; color: #2C6E49; margin-bottom: 0;'>{TXT['title']}</h1>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 0;'>", unsafe_allow_html=True)

# 读取数据
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

# CSS 美化（强制覆盖红色标签 + 修复边框 + 背景）
st.markdown("""

""", unsafe_allow_html=True)


# 翻译映射字典（英文 -> 中文）
TRANSLATIONS = {
    "Category": {
        "Idea to transform an unused space into a park": "将未使用空间改造成公园的建议",
        "Idea to upgrade an existing park": "升级现有公园的建议"
    },
    "Gender": {
        "Male": "男性",
        "Female": "女性",
        "Non-binary": "非二元性别",
        "Prefer not to say": "不愿透露",
        "Prefer to self-identify": "自我认同"
    },
    
    "Relationship": {
        "I live in the area": "我住在该地区",
        "I work in the area": "我在该地区工作",
        "I shop in the area": "我在该地区购物",
        "I travel to or through the area often": "我经常经过该地区",
        "I have friends and family in the area": "我在该地区有亲友",
        "I grew up in the area": "我在该地区长大",
        "I am studying or training in the area": "我在该地区上学或接受培训",
        "I own a business in the area": "我在该地区拥有企业"
    },

    "Age": {
        "Under 18": "18岁以下",
        "18-20": "18-20岁",
        "21-30": "21-30岁",
        "31-40": "31-40岁",
        "41-50": "41-50岁",
        "51-60": "51-60岁",
        "61-70": "61-70岁",
        "71 or older": "71岁及以上"
    }
}

# 将字段值替换为中文
def translate_column(df, column, lang):
    if lang == "中文" and column in TRANSLATIONS:
        return df[column].map(TRANSLATIONS[column]).fillna(df[column])
    return df[column]


# 筛选器
st.sidebar.header(TXT["filter_header"])

def dropdown_filter(label, options):
    options = sorted(options)
    selected = st.sidebar.multiselect(label, options, default=options)
    return selected

categories = dropdown_filter(TXT["category"], translate_column(df, "Category", "English").dropna().unique())
ages = dropdown_filter(TXT["age"], translate_column(df, "Age", "English").dropna().unique())
genders = dropdown_filter(TXT["gender"], translate_column(df, "Gender", "English").dropna().unique())
relations = dropdown_filter(TXT["relationship"], translate_column(df, "Relationship", "English").dropna().unique())

filtered_df = df[
    translate_column(df, "Category", "English").isin(categories) &
    translate_column(df, "Age", "English").isin(ages) &
    translate_column(df, "Gender", "English").isin(genders) &
    translate_column(df, "Relationship", "English").isin(relations)
]

# 地图（默认样式）


st.markdown("""
    <style>
        .element-container:has(iframe) {
            margin-bottom: -40px;
        }
    </style>
""", unsafe_allow_html=True)



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

    
if not filtered_df.empty:
       st_folium(m, height=500, use_container_width=True)
else:
        st.warning(TXT["no_result"])

# 图表绘制函数
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


from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import tempfile

# 导出图表为分页 PDF（每页2图）
def export_pdf(category_fig, age_fig, gender_fig, relationship_fig):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    chart_h = (height - 3 * margin) / 2  # 2 charts per page

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


# 图表展示（两列）
if not filtered_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(TXT["charts"]["category"])
        cat_fig = plot_bar_with_labels(translate_column(filtered_df, "Category", "English").value_counts(), TXT["charts"]["category"], TXT["category"])
        st.pyplot(cat_fig)

    with col2:
        st.markdown(TXT["charts"]["age"])
        age_fig = plot_bar_with_labels(translate_column(filtered_df, "Age", "English").value_counts().sort_index(), TXT["charts"]["age"], TXT["age"])
        st.pyplot(age_fig)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(TXT["charts"]["gender"])
        gender_counts = translate_column(filtered_df, "Gender", "English").value_counts()
        fig1, ax1 = plt.subplots()
        wedges, texts, autotexts = ax1.pie(gender_counts, labels=gender_counts.index, autopct="%1.1f%%", startangle=90)
        for text in texts + autotexts:
            text.set_fontsize(10)
        ax1.axis("equal")
        ax1.set_title(TXT["charts"]["gender"], fontsize=13, color="#2C6E49", pad=10)
        st.pyplot(fig1)

    with col4:
        st.markdown(TXT["charts"]["relationship"])
        rel_fig = plot_bar_with_labels(translate_column(filtered_df, "Relationship", "English").value_counts(), TXT["charts"]["relationship"], TXT["relationship"])
        st.pyplot(rel_fig)

    if st.button(TXT["export"]):
        pdf_buffer = export_pdf(cat_fig, age_fig, fig1, rel_fig)
        st.download_button(
            label=TXT["export_btn"],
            data=pdf_buffer,
            file_name="park_suggestions_charts.pdf",
            mime="application/pdf"
        )

# 触发 rerun（避免中间断流）
if st.session_state.refresh_count <= 2:
    st.experimental_rerun()
