# Comfort Linechart Visualization (PMV / PPD)

This module creates monthly line charts for **PMV** and **PPD** comfort indicators
across different building zones, including min/max bands and comfort reference ranges.

Generated using **Bokeh**.

---

## 📥 Input Format

The Manager generates two files:

PMV Data.xlsx
PPD Data.xlsx


Both have the structure:

| Month | Zone1 | Zone1min | Zone1max | Zone2 | Zone2min | ... |
|-------|-------|----------|----------|-------|----------|-----|

---

## 📊 Output

The module outputs:

PMV_Monthly.html
PPD_Monthly.html


Features:
- min/max envelopes
- ISO 7730 and ASHRAE 55 comfort zones
- interactive hover
- legend with click-to-hide zones

---

## 🧩 Dependencies

- Bokeh  
- Pandas  
- Colorcet  

---

## 🚀 How It Works

Run manually:

```python
from Linechart import lnchrt
lnchrt("PMV Data.xlsx", ["Zone1","Zone2"], target="PMV")

In full workflow, the Manager runs this automatically.