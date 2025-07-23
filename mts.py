import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="MTS Post-Processing Tool", layout="wide")
st.title("MTS Post-Processing Tool")

uploaded = st.file_uploader(
    "Upload one or more .lho or .txt files",
    type=['lho', 'txt'],
    accept_multiple_files=True
)

if not uploaded:
    st.info("📂 Please upload at least one file to continue.")
    st.stop()

for file in uploaded:
    raw = file.getvalue().decode('latin-1').splitlines()
    start = next(i for i, L in enumerate(raw) if L.strip() == '-- FIN ZONAS --') + 1
    end   = next(i for i, L in enumerate(raw) if L.strip() == '-- FIN MEDIDAS --')
    section = raw[start:end]

    rows = []
    for ln in section:
        parts = re.split(r'\s+', ln.strip())
        if len(parts) < 7:
            continue
        cable, layer, wire, zone = parts[:4]
        force    = parts[4]
        distance = parts[-2]
        valid    = parts[-1]
        rows.append([cable, layer, wire, zone, force, distance, valid])

    df = pd.DataFrame(rows, columns=['Cable','Layer','Wire','Zone','Force','Distance','Valid'])
    for col in ['Cable','Layer','Zone','Force','Distance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Force'])

    zone1 = df[df['Zone'] == 1]
    avg = zone1.groupby(['Cable','Layer'], as_index=False)['Force'].mean()
    piv = avg.pivot(index='Cable', columns='Layer', values='Force')
    piv.columns = [f'C{int(c)}' for c in piv.columns]
    piv = piv.round(1)
    piv.index.name = 'Ass.'
    base = piv.reset_index()

    avg_row = piv.mean().to_frame().T
    avg_row.insert(0, 'Ass.', 'Average')
    std_row = piv.std().to_frame().T
    std_row.insert(0, 'Ass.', 'Std Dev')

    result = pd.concat(
        [base, avg_row.round(1), std_row.round(1)],
        ignore_index=True
    )

    st.markdown(f"### {file.name}")
    st.write(
        result
          .style
          .hide(axis="index")
          .format(precision=1)
    )
