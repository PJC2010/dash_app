import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime

##commit

st.set_page_config(
    page_title="Medication Adherence Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2563EB;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #4B5563;
    }
    .highlight {
        background-color: #DBEAFE;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # Replace with your actual file path
        df = pd.read_csv('steamlit_dashboard\QS_Q1_Outcomes_3_10_25.csv')
        
        # Convert Last Activity Date to datetime and handle errors
        df["Last Activity Date"] = pd.to_datetime(df["Last Activity Date"], errors='coerce')
        
        # Drop rows with invalid dates
        df = df.dropna(subset=["Last Activity Date"])
        
        # Extract month information safely
        df["Month"] = df["Last Activity Date"].dt.month
        
        # Convert month to integer before looking up month name
        df["Month Name"] = df["Month"].apply(lambda x: calendar.month_name[int(x)])
        
        # Use isocalendar() safely
        try:
            df["Week"] = df["Last Activity Date"].dt.isocalendar().week
        except:
            # Fallback for older pandas versions
            df["Week"] = df["Last Activity Date"].dt.week
            
        # Filter out specific markets
        excluded_markets = ['Chicago', 'LasVegas', 'NewHampshire', 'NewJersey', 'NrthIndiana']
        df = df[~df['MarketCode'].isin(excluded_markets)]
        
        # Check for and create success metrics if they don't exist
        if "Intervention Successful" not in df.columns:
            # Create a sample success metric if it doesn't exist in your data
            # In a real scenario, this should be based on your business logic
            df["Intervention Successful"] = (df["Gap Status"] == "Gap Worked")
        
        # Check for and create financial metrics if they don't exist
        if "Estimated Savings" not in df.columns:
            # Create placeholder financial metrics for demo purposes
            df["Estimated Savings"] = df["Intervention Successful"].apply(
                lambda x: np.random.randint(1000, 5000) if x else 0
            )
        
        if "Intervention Cost" not in df.columns:
            # Create placeholder cost metrics
            # In a real scenario, this would be based on your intervention types
            intervention_costs = {
                "Phone outreach": 25,
                "Mail reminder": 10,
                "Pharmacy coordination": 40,
                "Provider outreach": 50,
                "Benefits review": 35,
                "Educational materials": 15,
                "Medication therapy management": 75,
                "Transportation assistance": 100,
                "Financial assistance": 150,
                "Simplified regimen": 30,
                "No intervention": 0
            }
            
            # Use a default cost if the Quality Specialist Intervention column doesn't exist
            if "Quality Specialist Intervention" in df.columns:
                df["Intervention Cost"] = df["Quality Specialist Intervention"].map(
                    lambda x: intervention_costs.get(x, 30) if pd.notna(x) else 30
                )
            else:
                df["Intervention Cost"] = 30
        
        # Check for and create Time to Resolution if it doesn't exist
        if "Time to Resolution" not in df.columns:
            # Create a placeholder for demo purposes
            df["Time to Resolution"] = np.random.randint(1, 30, len(df))
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load the data
df = load_data()

if df.empty:
    st.error("No data available. Please check your data file and try again.")
    st.stop()

# Define month order for sorting
month_order = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]

# Sidebar filters
st.sidebar.markdown("## Dashboard Filters")

# Date range filter
min_date = df["Last Activity Date"].min().date()
max_date = df["Last Activity Date"].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Convert to datetime for filtering
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df["Last Activity Date"].dt.date >= start_date) & 
                    (df["Last Activity Date"].dt.date <= end_date)]
else:
    filtered_df = df
    start_date = min_date
    end_date = max_date

# Market filter
markets = ["All"] + sorted(df["MarketCode"].unique().tolist())
selected_market = st.sidebar.selectbox("Market", markets)
if selected_market != "All":
    filtered_df = filtered_df[filtered_df["MarketCode"] == selected_market]

# Medication Type filter
if "MedAdherenceMeasureCode" in df.columns:
    med_types = ["All"] + df["MedAdherenceMeasureCode"].unique().tolist()
    selected_med_type = st.sidebar.selectbox("Medication Type", med_types)
    if selected_med_type != "All":
        filtered_df = filtered_df[filtered_df["MedAdherenceMeasureCode"] == selected_med_type]

# Payer filter
if "PayerCode" in df.columns:
    payers = ["All"] + df["PayerCode"].unique().tolist()
    selected_payer = st.sidebar.selectbox("Payer", payers)
    if selected_payer != "All":
        filtered_df = filtered_df[filtered_df["PayerCode"] == selected_payer]

# Main dashboard
st.markdown("<div class='main-header'>Medication Adherence Program Dashboard</div>", unsafe_allow_html=True)
st.markdown(f"**Reporting Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
           unsafe_allow_html=True)

# Metrics row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

# Metric 1: Total gaps
total_gaps = len(filtered_df)
with metric_col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{total_gaps:,}</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Total Adherence Gaps</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Metric 2: Gap closure rate
worked_gaps = filtered_df[filtered_df["Gap Status"] == "Gap Worked"]
gap_closure_rate = len(worked_gaps[worked_gaps["Intervention Successful"]]) / len(worked_gaps) if len(worked_gaps) > 0 else 0
with metric_col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{gap_closure_rate:.1%}</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Gap Closure Rate</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Metric 3: Worked vs. Not Worked
worked_pct = len(filtered_df[filtered_df["Gap Status"] == "Gap Worked"]) / total_gaps if total_gaps > 0 else 0
with metric_col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{worked_pct:.1%}</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Gaps Worked</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Metric 4: ROI
total_savings = filtered_df["Estimated Savings"].sum()
total_costs = filtered_df["Intervention Cost"].sum()
roi = (total_savings - total_costs) / total_costs if total_costs > 0 else 0
with metric_col4:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{roi:.1f}x</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Program ROI</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Row 1: Performance & Intervention Effectiveness
st.markdown("<div class='sub-header'>Performance & Intervention Effectiveness</div>", unsafe_allow_html=True)
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    try:
        monthly_data = filtered_df.groupby("Month Name").apply(
            lambda x: len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0
        ).reset_index()
        monthly_data.columns = ["Month", "Success Rate"]
        
        monthly_data["Month_num"] = monthly_data["Month"].apply(lambda x: month_order.index(x) if x in month_order else 0)
        monthly_data = monthly_data.sort_values("Month_num")
        
        fig = px.line(
            monthly_data, 
            x="Month", 
            y="Success Rate",
            markers=True,
            title="Gap Closure Rate by Month",
            labels={"Success Rate": "Closure Rate"},
            color_discrete_sequence=["#2563EB"]
        )
        fig.update_layout(
            height=350,
            yaxis=dict(tickformat=".0%"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating monthly performance chart: {str(e)}")
        st.info("Please check that your data contains the necessary columns.")

with row1_col2:
    try:
        if "Quality Specialist Intervention" in filtered_df.columns:
            intervention_success = filtered_df.groupby("Quality Specialist Intervention").apply(
                lambda x: {
                    "Success Rate": len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0,
                    "Count": len(x)
                }
            ).reset_index()
            
            intervention_success["Success Rate"] = intervention_success[0].apply(lambda x: x["Success Rate"])
            intervention_success["Count"] = intervention_success[0].apply(lambda x: x["Count"])
            intervention_success = intervention_success.drop(0, axis=1)
            
            intervention_success = intervention_success.sort_values("Success Rate", ascending=False)
            
            fig = px.bar(
                intervention_success,
                x="Success Rate",
                y="Quality Specialist Intervention",
                color="Count",
                color_continuous_scale="Blues",
                title="Intervention Effectiveness by Type",
                labels={"Quality Specialist Intervention": "Intervention Type"}
            )
            fig.update_layout(
                height=350,
                xaxis=dict(tickformat=".0%"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Intervention effectiveness chart not available: Missing 'Quality Specialist Intervention' column.")
    except Exception as e:
        st.error(f"Error generating intervention effectiveness chart: {str(e)}")

# Row 2: Operational Efficiency
st.markdown("<div class='sub-header'>Operational Efficiency & Resource Utilization</div>", unsafe_allow_html=True)
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    try:
        gap_status_counts = filtered_df["Gap Status"].value_counts().reset_index()
        gap_status_counts.columns = ["Status", "Count"]
        
        fig = px.pie(
            gap_status_counts,
            values="Count",
            names="Status",
            title="Gap Status Overview",
            color_discrete_sequence=["#2563EB", "#DBEAFE"]
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hole=0.4
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating gap status chart: {str(e)}")

with row2_col2:
    try:
        resolution_time = filtered_df.groupby("MarketCode")["Time to Resolution"].agg(
            ["mean", "median", "count"]
        ).reset_index()
        resolution_time.columns = ["Market", "Mean Days", "Median Days", "Count"]
        resolution_time = resolution_time.sort_values("Mean Days")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=resolution_time["Market"],
            y=resolution_time["Mean Days"],
            name="Mean Days",
            marker_color="#2563EB"
        ))
        fig.add_trace(go.Bar(
            x=resolution_time["Market"],
            y=resolution_time["Median Days"],
            name="Median Days",
            marker_color="#93C5FD"
        ))
        fig.update_layout(
            title="Resolution Time by Market",
            height=350,
            barmode="group",
            xaxis_title="Market",
            yaxis_title="Days to Resolution"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating resolution time chart: {str(e)}")

# Row 3: Root Cause Analysis
st.markdown("<div class='sub-header'>Root Cause Analysis</div>", unsafe_allow_html=True)
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    try:
        if "Barrier Identified" in filtered_df.columns:
            barriers = filtered_df["Barrier Identified"].value_counts().reset_index()
            barriers.columns = ["Barrier", "Count"]
            barriers = barriers.sort_values("Count", ascending=False).head(10)
            
            fig = px.bar(
                barriers,
                x="Count",
                y="Barrier",
                title="Top 10 Barriers to Medication Adherence",
                color="Count",
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                height=350,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Barriers chart not available: Missing 'Barrier Identified' column.")
    except Exception as e:
        st.error(f"Error generating barriers chart: {str(e)}")

with row3_col2:
    try:
        geo_issues = filtered_df.groupby("MarketCode").size().reset_index()
        geo_issues.columns = ["Market", "Gap Count"]
        
        total = geo_issues["Gap Count"].sum()
        geo_issues["Percentage"] = geo_issues["Gap Count"] / total
        
        fig = px.bar(
            geo_issues,
            x="Market",
            y="Gap Count",
            color="Percentage",
            color_continuous_scale="Blues",
            title="Geographic Distribution of Adherence Gaps"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating geographic distribution chart: {str(e)}")

# Row 4: Strategic Indicators
st.markdown("<div class='sub-header'>Strategic Indicators</div>", unsafe_allow_html=True)
row4_col1, row4_col2 = st.columns(2)

with row4_col1:
    try:
        if "Escalation" in filtered_df.columns and "Escalation Outcome" in filtered_df.columns:
            escalation_data = filtered_df[filtered_df["Escalation"] == "Yes"]
            escalation_outcomes = escalation_data["Escalation Outcome"].value_counts().reset_index()
            escalation_outcomes.columns = ["Outcome", "Count"]
            
            total_escalations = len(escalation_data)
            non_escalated = len(filtered_df) - total_escalations
            
            # Create a multi-stage funnel chart
            stages = ["Total Gaps", "Escalated", "Resolved", "Failed", "Pending", "Referred"]
            values = [
                len(filtered_df),
                total_escalations,
                len(escalation_data[escalation_data["Escalation Outcome"] == "Resolved"]),
                len(escalation_data[escalation_data["Escalation Outcome"] == "Failed to resolve"]),
                len(escalation_data[escalation_data["Escalation Outcome"] == "Pending"]),
                len(escalation_data[escalation_data["Escalation Outcome"] == "Referred to case management"])
            ]
            
            fig = go.Figure()
            fig.add_trace(go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial",
                marker={"color": ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", "#DBEAFE"]}
            ))
            fig.update_layout(
                title="Escalation Funnel Analysis",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Escalation funnel not available: Missing escalation columns.")
    except Exception as e:
        st.error(f"Error generating escalation funnel: {str(e)}")

with row4_col2:
    try:
        if "MedAdherenceMeasureCode" in filtered_df.columns and "NDCDesc" in filtered_df.columns:
            med_analysis = filtered_df.groupby(["MedAdherenceMeasureCode", "NDCDesc"]).size().reset_index()
            med_analysis.columns = ["Med Type", "Medication", "Count"]
            
            # Add intervention success information
            med_success = filtered_df.groupby(["MedAdherenceMeasureCode", "NDCDesc"]).apply(
                lambda x: len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0
            ).reset_index()
            med_success.columns = ["Med Type", "Medication", "Success Rate"]
            
            # Merge the dataframes
            med_analysis = med_analysis.merge(med_success, on=["Med Type", "Medication"])
            
            fig = px.treemap(
                med_analysis,
                path=[px.Constant("All"), "Med Type", "Medication"],
                values="Count",
                color="Success Rate",
                color_continuous_scale="Blues",
                title="Medication Adherence Gap Analysis"
            )
            fig.update_layout(
                height=350,
                coloraxis_colorbar=dict(
                    title="Success Rate",
                    tickformat=".0%"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Medication analysis not available: Missing medication columns.")
    except Exception as e:
        st.error(f"Error generating medication analysis chart: {str(e)}")

# Row 5: Provider and Payer Analysis
st.markdown("<div class='sub-header'>Provider & Payer Analysis</div>", unsafe_allow_html=True)
row5_col1, row5_col2 = st.columns(2)

with row5_col1:
    try:
        if "Provider" in filtered_df.columns:
            provider_data = filtered_df.groupby("Provider").apply(
                lambda x: {
                    "Gap Count": len(x),
                    "Success Rate": len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0
                }
            ).reset_index()
            
            provider_data["Gap Count"] = provider_data[0].apply(lambda x: x["Gap Count"])
            provider_data["Success Rate"] = provider_data[0].apply(lambda x: x["Success Rate"])
            provider_data = provider_data.drop(0, axis=1)
            
            # Sort and take top 15 by gap count for readability
            top_providers = provider_data.sort_values("Gap Count", ascending=False).head(15)
            
            fig = px.scatter(
                top_providers,
                x="Gap Count",
                y="Success Rate",
                color="Success Rate",
                color_continuous_scale="Blues",
                size="Gap Count",
                hover_name="Provider",
                title="Provider Analysis: Gap Volume vs. Success Rate (Top 15)"
            )
            fig.update_layout(
                height=350,
                yaxis=dict(tickformat=".0%")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Provider analysis not available: Missing 'Provider' column.")
    except Exception as e:
        st.error(f"Error generating provider analysis chart: {str(e)}")

with row5_col2:
    try:
        if "PayerCode" in filtered_df.columns:
            payer_data = filtered_df.groupby("PayerCode").apply(
                lambda x: {
                    "Gap Count": len(x),
                    "Success Rate": len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0,
                    "Avg Resolution Time": x["Time to Resolution"].mean()
                }
            ).reset_index()
            
            payer_data["Gap Count"] = payer_data[0].apply(lambda x: x["Gap Count"])
            payer_data["Success Rate"] = payer_data[0].apply(lambda x: x["Success Rate"])
            payer_data["Avg Resolution Time"] = payer_data[0].apply(lambda x: x["Avg Resolution Time"])
            payer_data = payer_data.drop(0, axis=1)
            
            # Sort by gap count
            payer_data = payer_data.sort_values("Gap Count", ascending=False)
            
            fig = go.Figure(data=[
                go.Bar(
                    name="Gap Count",
                    x=payer_data["PayerCode"],
                    y=payer_data["Gap Count"],
                    marker_color="#3B82F6",
                    yaxis="y"
                ),
                go.Scatter(
                    name="Success Rate",
                    x=payer_data["PayerCode"],
                    y=payer_data["Success Rate"],
                    mode="lines+markers",
                    marker=dict(color="darkblue"),
                    line=dict(color="darkblue"),
                    yaxis="y2"
                )
            ])
            
            fig.update_layout(
                title="Payer Analysis: Gap Volume and Success Rate",
                height=350,
                yaxis=dict(
                    title="Gap Count",
                    side="left"
                ),
                yaxis2=dict(
                    title="Success Rate",
                    side="right",
                    overlaying="y",
                    tickformat=".0%",
                    range=[0, 1]
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Payer analysis not available: Missing 'PayerCode' column.")
    except Exception as e:
        st.error(f"Error generating payer analysis chart: {str(e)}")

# Row 6: Financial Impact Analysis
st.markdown("<div class='sub-header'>Financial Impact Analysis</div>", unsafe_allow_html=True)
row6_col1, row6_col2 = st.columns(2)

with row6_col1:
    try:
        monthly_roi = filtered_df.groupby("Month Name").apply(
            lambda x: {
                "Savings": x["Estimated Savings"].sum(),
                "Costs": x["Intervention Cost"].sum(),
                "ROI": (x["Estimated Savings"].sum() - x["Intervention Cost"].sum()) / x["Intervention Cost"].sum() if x["Intervention Cost"].sum() > 0 else 0
            }
        ).reset_index()
        
        monthly_roi["Savings"] = monthly_roi[0].apply(lambda x: x["Savings"])
        monthly_roi["Costs"] = monthly_roi[0].apply(lambda x: x["Costs"])
        monthly_roi["ROI"] = monthly_roi[0].apply(lambda x: x["ROI"])
        monthly_roi = monthly_roi.drop(0, axis=1)
        
        monthly_roi["Month_num"] = monthly_roi["Month Name"].apply(lambda x: month_order.index(x) if x in month_order else 0)
        monthly_roi = monthly_roi.sort_values("Month_num")
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=monthly_roi["Month Name"],
                y=monthly_roi["Savings"],
                name="Estimated Savings",
                marker_color="#2563EB"
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Bar(
                x=monthly_roi["Month Name"],
                y=monthly_roi["Costs"],
                name="Program Costs",
                marker_color="#93C5FD"
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=monthly_roi["Month Name"],
                y=monthly_roi["ROI"],
                name="ROI",
                mode="lines+markers",
                marker=dict(color="darkblue"),
                line=dict(color="darkblue")
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Monthly Financial Impact",
            height=350,
            barmode="group",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="Dollar Amount ($)", secondary_y=False)
        fig.update_yaxes(title_text="Return on Investment", tickformat=".1f", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating monthly financial impact chart: {str(e)}")

with row6_col2:
    try:
        if "Barrier Identified" in filtered_df.columns:
            barrier_roi = filtered_df.groupby("Barrier Identified").apply(
                lambda x: {
                    "Count": len(x),
                    "Success Rate": len(x[x["Intervention Successful"]]) / len(x) if len(x) > 0 else 0,
                    "Avg Cost": x["Intervention Cost"].mean(),
                    "Total Savings": x["Estimated Savings"].sum()
                }
            ).reset_index()
            
            barrier_roi["Count"] = barrier_roi[0].apply(lambda x: x["Count"])
            barrier_roi["Success Rate"] = barrier_roi[0].apply(lambda x: x["Success Rate"])
            barrier_roi["Avg Cost"] = barrier_roi[0].apply(lambda x: x["Avg Cost"])
            barrier_roi["Total Savings"] = barrier_roi[0].apply(lambda x: x["Total Savings"])
            barrier_roi = barrier_roi.drop(0, axis=1)
            
            barrier_roi["ROI per Gap"] = barrier_roi["Total Savings"] / (barrier_roi["Avg Cost"] * barrier_roi["Count"])
            barrier_roi = barrier_roi.sort_values("ROI per Gap", ascending=False)
            
            fig = px.bar(
                barrier_roi.head(10),
                x="ROI per Gap",
                y="Barrier Identified",
                color="Success Rate",
                color_continuous_scale="Blues",
                hover_data=["Count", "Avg Cost", "Total Savings"],
                title="Most Cost-Effective Barriers to Address"
            )
            fig.update_layout(
                height=350,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Barrier ROI analysis not available: Missing 'Barrier Identified' column.")
    except Exception as e:
        st.error(f"Error generating barrier ROI chart: {str(e)}")

