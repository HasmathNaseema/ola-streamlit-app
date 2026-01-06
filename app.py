import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

from db import run_query


@st.cache_data(ttl=300)
def get_distinct_values(col_name: str):
    q = f"""
        SELECT DISTINCT {col_name} AS val
        FROM ola_clean
        WHERE {col_name} IS NOT NULL
        ORDER BY val;
    """
    df = run_query(q)
    return df["val"].dropna().astype(str).tolist()


SQL_FILE = "ola_sql_queries.sql"   # must match your file name

st.set_page_config(page_title="OLA Analytics", layout="wide")
st.title("OLA Analytics App")
st.caption(f"Run saved SQL queries from **{SQL_FILE}** with MySQL filters ✅")

tab1, tab2 = st.tabs(["🧾 SQL Explorer", "📊 Power BI Dashboard"])

with tab2:
    st.subheader("Power BI Dashboard")
    powerbi_url = "PASTE_YOUR_POWERBI_PUBLISH_TO_WEB_URL_HERE"
    st.components.v1.iframe(powerbi_url, height=750, scrolling=True)


    
def load_named_queries(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    queries = {}
    current_name = None
    current_sql_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("-- name:"):
            if current_name and current_sql_lines:
                queries[current_name] = "".join(current_sql_lines).strip()

            current_name = stripped.split(":", 1)[1].strip()
            current_sql_lines = []
        else:
            if current_name and stripped != "":
                current_sql_lines.append(line)

    if current_name and current_sql_lines:
        queries[current_name] = "".join(current_sql_lines).strip()

    return queries
with tab1:
    st.subheader("SQL Explorer")
# ---------- Load queries ----------
    try:
        named_queries = load_named_queries(SQL_FILE)
    except FileNotFoundError:
        st.error(f"Could not find `{SQL_FILE}` in this folder. Put it next to app.py")
        st.stop()

    if not named_queries:
        st.warning("No queries found. Make sure each query starts with `-- name:` and has SQL below it.")
        st.stop()

    query_name = st.selectbox("Choose a query", list(named_queries.keys()))
    base_sql = named_queries[query_name]

    with st.expander("See Base SQL", expanded=False):
        st.code(base_sql, language="sql")

    # ---------- Sidebar Filters ----------
    st.sidebar.header("Filters (Applied in MySQL)")

    status_filter = st.sidebar.multiselect(
        "Booking Status",
        ["Success", "Canceled by Driver", "Canceled by Customer", "Driver Not Found"],
    )

    vehicle_filter = st.sidebar.multiselect(
        "Vehicle Type",
        ["Auto", "Bike", "Mini", "Prime Sedan", "Prime SUV", "Prime Plus", "eBike"],
    )
    # --- NEW: Payment Method filter (from DB) ---
    payment_method_options = get_distinct_values("Payment_Method")
    payment_filter = st.sidebar.multiselect("Payment Method", payment_method_options)

    # --- NEW: Cancelled By filter (Customer / Driver) ---
    cancel_source_filter = st.sidebar.multiselect("Cancelled By", ["Customer", "Driver"])

    # --- NEW: Ratings filters ---
    use_rating_filters = st.sidebar.checkbox("Use Ratings Filter", value=False)
    exclude_blank_ratings = st.sidebar.checkbox("Exclude blank ratings", value=True)

    driver_min = driver_max = cust_min = cust_max = None
    if use_rating_filters:
        driver_min, driver_max = st.sidebar.slider("Driver Ratings", 0.0, 5.0, (0.0, 5.0), 0.1)
        cust_min, cust_max     = st.sidebar.slider("Customer Rating", 0.0, 5.0, (0.0, 5.0), 0.1)

    date_filter_on = st.sidebar.checkbox("Use Date Range Filter", value=False)
    start_date = None
    end_date = None
    if date_filter_on:
        start_date = st.sidebar.date_input("Start Date")
        end_date = st.sidebar.date_input("End Date")

    # ---------- Build WHERE clause safely ----------
    where_clauses = []
    params = {}

    # Booking_Status (only if NOT using cancel_source_filter)
    if status_filter and not cancel_source_filter:
        placeholders = []
        for i, v in enumerate(status_filter):
            key = f"status_{i}"
            placeholders.append(f":{key}")
            params[key] = v
        where_clauses.append(f"Booking_Status IN ({', '.join(placeholders)})")

    # Vehicle_Type
    if vehicle_filter:
        placeholders = []
        for i, v in enumerate(vehicle_filter):
            key = f"veh_{i}"
            placeholders.append(f":{key}")
            params[key] = v
        where_clauses.append(f"Vehicle_Type IN ({', '.join(placeholders)})")

    # Date range
    if date_filter_on and start_date and end_date:
        where_clauses.append("DATE(`Date`) BETWEEN :start_date AND :end_date")
        params["start_date"] = str(start_date)
        params["end_date"] = str(end_date)
    # Payment_Method
    if payment_filter:
        placeholders = []
        for i, v in enumerate(payment_filter):
            key = f"pay_{i}"
            placeholders.append(f":{key}")
            params[key] = v
        where_clauses.append(f"Payment_Method IN ({', '.join(placeholders)})")

    # Cancellation Source (maps to Booking_Status)
    if cancel_source_filter:
        cancel_map = {
            "Customer": "Canceled by Customer",
            "Driver": "Canceled by Driver"
        }
        cancel_status_values = [cancel_map[s] for s in cancel_source_filter]

        placeholders = []
        for i, v in enumerate(cancel_status_values):
            key = f"cancel_{i}"
            placeholders.append(f":{key}")
            params[key] = v
        where_clauses.append(f"Booking_Status IN ({', '.join(placeholders)})")

    # Ratings filters
    if use_rating_filters:
        if exclude_blank_ratings:
            where_clauses.append("Driver_Ratings IS NOT NULL")
            where_clauses.append("Customer_Rating IS NOT NULL")

        where_clauses.append("Driver_Ratings BETWEEN :driver_min AND :driver_max")
        where_clauses.append("Customer_Rating BETWEEN :cust_min AND :cust_max")

        params["driver_min"] = float(driver_min)
        params["driver_max"] = float(driver_max)
        params["cust_min"] = float(cust_min)
        params["cust_max"] = float(cust_max)


    # ---------- Combine final SQL ----------
    final_sql = base_sql.strip().rstrip(";").strip()

    # Split query into HEAD and TAIL so we can inject WHERE before GROUP BY / HAVING / ORDER BY / LIMIT
    m = re.search(r"\b(group\s+by|having|order\s+by|limit)\b", final_sql, flags=re.IGNORECASE)

    if m:
        head = final_sql[:m.start()].rstrip()
        tail = " " + final_sql[m.start():].lstrip()
    else:
        head, tail = final_sql, ""

    # Check WHERE only in the head (outer query part)
    has_where = re.search(r"\bwhere\b", head, flags=re.IGNORECASE) is not None

    if where_clauses:
        head += (" AND " if has_where else " WHERE ") + " AND ".join(where_clauses)

    final_sql = head + tail + ";"

    # ---------- Show Final SQL + Params ----------
    with st.expander("Final SQL (with filters)", expanded=False):
        st.code(final_sql, language="sql")
        st.write("Params:", params)

    # ---------- Run ----------
    run = st.button("Run Query ✅")

    if run:
        try:
            df = run_query(final_sql, params=params)
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Query failed ❌")
            st.exception(e)
