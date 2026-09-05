import re
import pandas as pd
import streamlit as st

# --- PAGE CONFIGURATION & PROFESSIONAL STYLING ---
st.set_page_config(
    page_title="Lab Solution & Buffer Calculator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a clean, executive-level laboratory aesthetic
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .protocol-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE ---
PROTOCOLS_DATABASE = [
    {
        "id": "pbs_001",
        "name": "Phosphate-Buffered Saline (PBS)",
        "aliases": ["pbs", "1x pbs", "phosphate buffered saline"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "ingredients": [
            {"name": "NaCl (Sodium chloride)", "amount": 8.0, "unit": "g", "concentration": "137 mM"},
            {"name": "KCl (Potassium chloride)", "amount": 0.2, "unit": "g", "concentration": "2.7 mM"},
            {"name": "Na2HPO4 (Sodium phosphate dibasic, Anhydrous)", "amount": 1.44, "unit": "g", "concentration": "10 mM"},
            {"name": "KH2PO4 (Potassium phosphate monobasic, Anhydrous)", "amount": 0.24, "unit": "g", "concentration": "1.8 mM"},
            {"name": "Ultrapure Water", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    },
    {
        "id": "dpbs_001",
        "name": "Dulbecco's Phosphate-Buffered Saline (DPBS)",
        "aliases": ["dpbs", "dulbeccos pbs", "dulbecco's pbs"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "ingredients": [
            {"name": "NaCl (Sodium chloride)", "amount": 8.0, "unit": "g", "concentration": "137 mM"},
            {"name": "KCl (Potassium chloride)", "amount": 0.20, "unit": "g", "concentration": "2.7 mM"},
            {"name": "Na2HPO4 (Sodium phosphate dibasic, Anhydrous)", "amount": 1.15, "unit": "g", "concentration": "8.1 mM"},
            {"name": "KH2PO4 (Potassium phosphate monobasic, Anhydrous)", "amount": 0.20, "unit": "g", "concentration": "1.47 mM"},
            {"name": "Ultrapure Water", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    },
    {
        "id": "tbs_001",
        "name": "Tris-Buffered Saline (TBS)",
        "aliases": ["tbs", "1x tbs", "tris buffered saline"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "ingredients": [
            {"name": "Tris base", "amount": 6.06, "unit": "g", "concentration": "50 mM"},
            {"name": "NaCl (Sodium chloride)", "amount": 8.76, "unit": "g", "concentration": "150 mM"},
            {"name": "Concentrated HCl (~37%, 12 N)", "amount": None, "unit": "Drops as needed for pH 7.6", "concentration": ""},
            {"name": "Ultrapure Water", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    },
    {
        "id": "tbst_001",
        "name": "Tris-Buffered Saline with Tween-20 (TBST)",
        "aliases": ["tbst", "tbs-t", "tbs tween"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "ingredients": [
            {"name": "1x TBS (pH 7.6)", "amount": 1000.0, "unit": "mL", "concentration": "Base Buffer"},
            {"name": "Tween-20", "amount": 1.0, "unit": "mL", "concentration": "0.1% v/v"}
        ]
    },
    {
        "id": "pbst_001",
        "name": "Phosphate-Buffered Saline with Tween-20 (PBST)",
        "aliases": ["pbst", "pbs-t", "pbs tween"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "ingredients": [
            {"name": "10× PBS Stock", "amount": 100.0, "unit": "mL", "concentration": "Final: 1×"},
            {"name": "Tween-20 (Polysorbate 20)", "amount": 1.0, "unit": "mL", "concentration": "0.1% v/v"},
            {"name": "Ultrapure Water", "amount": 900.0, "unit": "mL", "concentration": ""}
        ]
    },
    {
        "id": "tris_hcl_1m_001",
        "name": "Tris-HCl Buffer (1 M)",
        "aliases": ["tris-hcl 1m", "tris hcl 1m", "1m tris hcl", "tris hcl ph 7.4"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "protocol_concentration": 1.0,
        "protocol_concentration_unit": "M",
        "ingredients": [
            {"name": "Tris base (Molecular Biology Grade)", "amount": 121.1, "unit": "g", "concentration": "1 M"},
            {"name": "Concentrated HCl (~37%, 12 N)", "amount": None, "unit": "~70 mL (pH 7.4) or ~42 mL (pH 8.0)", "concentration": ""},
            {"name": "Ultrapure Water", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    },
    {
        "id": "mops_1m_001",
        "name": "MOPS Buffer (pH 7) 1 M",
        "aliases": ["mops 1m", "1m mops", "mops buffer"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "protocol_concentration": 1.0,
        "protocol_concentration_unit": "M",
        "ingredients": [
            {"name": "MOPS (Free Acid, RNase-free)", "amount": 209.3, "unit": "g", "concentration": "1 M"},
            {"name": "NaOH (10 N Solution)", "amount": None, "unit": "~30-40 mL (for pH 7.0)", "concentration": ""},
            {"name": "Ultrapure Water (DEPC-treated)", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    },
    {
        "id": "pipes_05m_001",
        "name": "PIPES Buffer (pH 6.8) 0.5 M",
        "aliases": ["pipes 0.5m", "0.5m pipes", "pipes buffer"],
        "category": "Buffer",
        "reference_volume": 1000.0,
        "reference_unit": "mL",
        "protocol_concentration": 0.5,
        "protocol_concentration_unit": "M",
        "ingredients": [
            {"name": "PIPES (Free Acid)", "amount": 151.2, "unit": "g", "concentration": "0.5 M"},
            {"name": "NaOH (Solid pellets OR 10 N liquid)", "amount": None, "unit": "~30-50 mL (to force dissolution)", "concentration": ""},
            {"name": "Ultrapure Water", "amount": None, "unit": "mL", "concentration": "", "is_top_up": True}
        ]
    }
]

# --- UTILITIES ---
def search_protocols(query):
    query_clean = query.strip().lower()
    if not query_clean:
        return PROTOCOLS_DATABASE
    matches = []
    for protocol in PROTOCOLS_DATABASE:
        if query_clean in protocol["name"].lower() or any(query_clean in alias for alias in protocol["aliases"]):
            matches.append(protocol)
    return matches

def convert_to_ml(value, unit):
    unit_lower = unit.strip().lower()
    if unit_lower in ['ul', 'µl']: 
        return value / 1000.0
    elif unit_lower == 'l': 
        return value * 1000.0
    return value

# --- UI LAYOUT ---

with st.sidebar:
    st.image("https://img.icons8.com/color/96/experimental-bottle.png", width=64)
    st.title("Lab Calculator")
    st.markdown("---")
    st.markdown("### Professional Module")
    st.info("This application calculates required chemical quantities based strictly on standardized laboratory reference protocols.")
    st.markdown("---")
    st.markdown("**Quick Filters**")
    selected_category = st.selectbox("Category", ["All Categories", "Buffer"])

st.title("Laboratory Solution & Media Calculator")
st.markdown("Search, scale, and generate precise preparation amounts for molecular biology and biochemistry workflows.")
st.markdown("---")

search_query = st.text_input("🔍 Search Protocols (e.g., PBS, TBS, MOPS, PIPES)", placeholder="Type protocol name or alias...")

matches = search_protocols(search_query)

if not matches:
    st.warning("No protocols found matching your search term. Please try another name or alias.")
else:
    protocol_names = [p["name"] for p in matches]
    selected_name = st.selectbox("Select Protocol from Database:", protocol_names)
    
    selected_protocol = next(p for p in matches if p["name"] == selected_name)

    st.markdown("### 📌 Reference Protocol Details")
    
    col_ref1, col_ref2, col_ref3 = st.columns(3)
    with col_ref1:
        st.metric("Reference Volume", f"{selected_protocol['reference_volume']} {selected_protocol['reference_unit']}")
    with col_ref2:
        st.metric("Category", selected_protocol.get("category", "Buffer"))
    with col_ref3:
        ref_c = selected_protocol.get("protocol_concentration")
        ref_u = selected_protocol.get("protocol_concentration_unit", "")
        st.metric("Base Concentration", f"{ref_c} {ref_u}" if ref_c else "Standard Formulation")

    ref_table_data = []
    for ing in selected_protocol["ingredients"]:
        amt_str = f"{ing['amount']} {ing['unit']}" if ing["amount"] is not None else ing["unit"]
        ref_table_data.append({
            "Material / Reagent": ing["name"],
            "Reference Amount": amt_str,
            "Concentration": ing.get("concentration", "")
        })
    
    with st.expander("View Original Reference Breakdown", expanded=False):
        st.dataframe(pd.DataFrame(ref_table_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    st.markdown("### ⚙️ Preparation Parameters")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        target_volume = st.number_input("Target Final Volume", min_value=0.1, value=500.0, step=10.0)
    with col_input2:
        target_unit = st.selectbox("Volume Unit", ["mL", "L", "µL"])

    ref_conc = selected_protocol.get("protocol_concentration")
    ref_unit = selected_protocol.get("protocol_concentration_unit", "")
    conc_scaling_factor = 1.0
    target_conc_display = ""

    if ref_conc is not None:
        st.info(f"💡 **Note:** The baseline formulation is formulated for **{ref_conc} {ref_unit}**. You can optionally adjust the target concentration below.")
        target_conc_value = st.number_input(f"Target Final Concentration ({ref_unit})", min_value=0.01, value=float(ref_conc), step=0.1)
        if target_conc_value != ref_conc:
            conc_scaling_factor = target_conc_value / ref_conc
            target_conc_display = f"{target_conc_value} {ref_unit}"

    target_volume_ml = convert_to_ml(target_volume, target_unit)
    vol_scaling_factor = target_volume_ml / selected_protocol['reference_volume']
    total_scaling_factor = vol_scaling_factor * conc_scaling_factor

    st.markdown("---")
    st.markdown("### 🧪 Required Materials & Quantities")

    calc_table_data = []
    for item in selected_protocol['ingredients']:
        if item.get('is_top_up'):
            req_amount = f"Up to {target_volume_ml:g} {item['unit']}"
        elif item['amount'] is not None:
            new_amount = round(item['amount'] * total_scaling_factor, 4)
            req_amount = f"{new_amount:g} {item['unit']}"
        else:
            req_amount = item['unit']
            
        final_conc = item.get('concentration', '')
        if final_conc and conc_scaling_factor != 1.0 and not item.get('is_top_up'):
            final_conc += f" (× {conc_scaling_factor:g})"
            
        calc_table_data.append({
            "Material / Reagent": item['name'],
            "Required Amount": req_amount,
            "Final Concentration": final_conc
        })

    df_calc = pd.DataFrame(calc_table_data)
    st.dataframe(df_calc, use_container_width=True, hide_index=True)

    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.metric("Total Scaling Factor", f"{total_scaling_factor:.4f}")
    with col_sum2:
        st.metric("Normalized Target Volume", f"{target_volume_ml:g} mL")

    csv_data = df_calc.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Preparation Sheet (CSV)",
        data=csv_data,
        file_name=f"{selected_protocol['id']}_{target_volume_ml}mL.csv",
        mime="text/csv",
    )
