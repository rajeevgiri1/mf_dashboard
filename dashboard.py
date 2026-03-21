import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="MUTUAL FUND - Kaunsa Din Sahi Hai", layout="wide")

# ==============================
# THEME
# ==============================
theme = st.sidebar.radio("🌗 Select Theme", ["Light", "Dark"])

if theme == "Dark":
    st.markdown("""
        <style>
        body { background-color: #0E1117; color: white; }
        </style>
    """, unsafe_allow_html=True)

# ==============================
# TITLE
# ==============================
st.title("📊 MUTUAL FUND - Kaunsa Din Sahi Hai")
st.markdown("### 💡 Sahi din choose karo, returns improve karo!")

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    df = pd.read_excel('MF_CAGR_Analysis_API_Names.xlsx')

    for col in ['1st year cagr', '2nd year cagr', '3rd year cagr']:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace('%', '', regex=False)
            .replace('N/A', '0')
            .astype(float)
        )

    return df

df = load_data()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("🔍 Filters")

schemes = df['scheme name'].unique()
default_schemes = schemes[:min(3, len(schemes))]

selected_schemes = st.sidebar.multiselect(
    "Select Schemes",
    options=schemes,
    default=default_schemes
)

metric = st.sidebar.selectbox(
    "Select Return Period",
    ["1st year cagr", "2nd year cagr", "3rd year cagr"]
)

filtered_df = df[df['scheme name'].isin(selected_schemes)].copy()

# ==============================
# DATE LOGIC (YOUR ORIGINAL)
# ==============================
if metric == "1st year cagr":
    start_date = "2019-01-01"
elif metric == "2nd year cagr":
    start_date = "2020-01-01"
else:
    start_date = "2021-01-01"

filtered_df['Date'] = pd.to_datetime(start_date) + pd.to_timedelta(
    filtered_df['Day of Month'] - 1, unit='D'
)

filtered_df['Date'] = filtered_df['Date'].dt.strftime('%d-%m-%y')

# ==============================
# CALCULATIONS
# ==============================
avg_cagr_per_day = filtered_df.groupby('Day of Month')[metric].mean().reset_index()

best_day = None
if not avg_cagr_per_day.empty:
    best_day = avg_cagr_per_day.loc[avg_cagr_per_day[metric].idxmax()]

# ==============================
# BEST DAY CHART
# ==============================
fig_avg = px.line(
    avg_cagr_per_day,
    x='Day of Month',
    y=metric,
    markers=True,
    text=metric
)

fig_avg.update_traces(textposition="top center")

if not avg_cagr_per_day.empty:
    y_min_avg = avg_cagr_per_day[metric].min()
    y_max_avg = avg_cagr_per_day[metric].max()

    buffer_avg = (y_max_avg - y_min_avg) * 0.1

    fig_avg.update_yaxes(range=[y_min_avg - buffer_avg, y_max_avg + buffer_avg])

    if best_day is not None:
        fig_avg.add_vline(
            x=best_day['Day of Month'],
            line_dash="dash",
            line_color="green"
        )

# ==============================
# HEATMAP
# ==============================
pivot_df = filtered_df.pivot(index='scheme name', columns='Day of Month', values=metric)

fig_heat = px.imshow(
    pivot_df,
    labels=dict(x="Day of Month", y="Scheme", color="CAGR (%)"),
    aspect="auto"
)

# ==============================
# 🔥 COMPARISON CHART (FIXED TIGHT SCALE)
# ==============================
y_min = filtered_df[metric].min()
y_max = filtered_df[metric].max()

# 👇 tighter compression (key fix)
buffer = (y_max - y_min) * 0.02   # only 2% instead of 10%

fig_comp = px.line(
    filtered_df,
    x='Day of Month',
    y=metric,
    color='scheme name',
    markers=True
)

fig_comp.update_yaxes(range=[y_min - buffer, y_max + buffer])

# ==============================
# DISTRIBUTION
# ==============================
fig_box = px.box(
    filtered_df,
    x='scheme name',
    y=metric,
    color='scheme name',
    points="all"
)

# ==============================
# TABS
# ==============================
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Home",
    "📊 Best Day Analysis",
    "🔥 Heatmap",
    "⚖️ Comparison",
    "📈 Distribution",
    "📋 Data Table",
    "📌 Insights & Download"
])

# ==============================
# HOME
# ==============================
with tab0:
    st.header("📌 About This Website")
    st.markdown("""
    This platform helps you identify the **best day of the month to invest in mutual funds**.

    ### What you can do:
    - Analyze return trends 📊  
    - Compare multiple schemes ⚖️  
    - Identify best investment day 📅  
    - Visualize data with charts 🔥  
    """)

# ==============================
# BEST DAY
# ==============================
with tab1:
    if best_day is not None:
        st.success(f"Best Day: {int(best_day['Day of Month'])} | Return: {best_day[metric]:.2f}%")
    st.plotly_chart(fig_avg, use_container_width=True)

# ==============================
# HEATMAP
# ==============================
with tab2:
    st.plotly_chart(fig_heat, use_container_width=True)

# ==============================
# COMPARISON
# ==============================
with tab3:
    st.plotly_chart(fig_comp, use_container_width=True)

# ==============================
# DISTRIBUTION
# ==============================
with tab4:
    st.plotly_chart(fig_box, use_container_width=True)

# ==============================
# DATA TABLE
# ==============================
with tab5:
    st.dataframe(
        filtered_df[['scheme name', 'Date', 'Day of Month', metric]],
        use_container_width=True
    )

# ==============================
# INSIGHTS + DOWNLOAD
# ==============================
with tab6:
    st.header("🏆 Best Day Per Scheme")

    best_per_scheme = []

    for scheme in selected_schemes:
        scheme_data = filtered_df[filtered_df['scheme name'] == scheme]

        if not scheme_data.empty:
            best_row = scheme_data.loc[scheme_data[metric].idxmax()]

            best_per_scheme.append({
                "Scheme": scheme,
                "Best Day": int(best_row['Day of Month']),
                "Return (%)": round(best_row[metric], 2)
            })

    st.dataframe(pd.DataFrame(best_per_scheme), use_container_width=True)

    st.header("⬇️ Download Report")

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "mutual_fund_analysis.csv", "text/csv")

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output) as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = to_excel(filtered_df)

    st.download_button(
        "Download Excel",
        excel_data,
        "mutual_fund_analysis.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )