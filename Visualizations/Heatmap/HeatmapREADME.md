# Heatmap Visualization

This module generates an interactive heatmap showing monthly or hourly variations
of any energy or environmental variable (temperature, RH, gains/losses, energy use).

The heatmap is produced using **Bokeh**, and reads a pre-processed Excel file
generated automatically by `BEPVis_Manager.py`.

---

## 📥 Input Format

The Manager creates a file named:

HEatmap_Data.xlsx

Expected structure:

| Month | Zone | Value |
|-------|------|--------|
| Jan   | Zone1 | 21.3 |
| Feb   | Zone1 | 20.7 |
| ...   | ...   | ... |

- `Month`: text label (Jan–Dec)
- `Zone`: zone or space name
- `Value`: temperature, RH, energy, etc.

---

## 📊 Output

The script generates:

Heatmap.html


Features:
- interactive hover tool
- zoom & pan
- color scale legend
- monthly and zone comparison

---

## 🧩 Dependencies

- Bokeh
- Pandas
- Colorcet (palette)

---

## 🚀 How It Works

Simply call the module from the Manager or manually:

```python
from Heatmap import htmap
htmap("Heatmap_Data.xlsx")

The Manager handles this automatically in normal operation.