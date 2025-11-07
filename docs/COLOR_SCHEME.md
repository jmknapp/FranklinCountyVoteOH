# Map Color Scheme

## US Political Convention

In all maps, the colors follow the standard US political convention:

- 🔵 **Blue = Democratic** (high D_share, Democratic swing)
- 🔴 **Red = Republican** (low D_share, Republican swing)

## Colormaps Used

### For Partisan Share (D_share)
- **Colormap:** `RdBu` (Red-Blue)
- **Range:** 0 (all Republican/red) to 1 (all Democratic/blue)
- **Interpretation:**
  - Dark red = Strong Republican (0-25%)
  - Light red = Lean Republican (25-50%)
  - Light blue = Lean Democratic (50-75%)
  - Dark blue = Strong Democratic (75-100%)

### For Partisan Swings
- **Colormap:** `RdBu` (Red-Blue, diverging)
- **Center:** 0 (no change)
- **Interpretation:**
  - Red = Republican shift (negative swing)
  - Blue = Democratic shift (positive swing)
  - White/neutral = No change

### For Turnout
- **Colormap:** `YlOrRd` (Yellow-Orange-Red, sequential)
- **Interpretation:**
  - Light yellow = Low turnout
  - Dark red = High turnout

## Note on RdBu vs RdBu_r

**IMPORTANT:** Do NOT use `RdBu_r` (reversed) for political maps!

- ❌ **`RdBu_r`**: Low=Blue, High=Red (BACKWARDS for US politics)
- ✅ **`RdBu`**: Low=Red, High=Blue (CORRECT for US politics)

The `_r` suffix in matplotlib colormaps means "reversed" - it flips the color scheme, which inverts the traditional political colors.

## Examples

### Correct Color Usage

```python
# Democratic share map
gdf.plot(column='D_share', cmap='RdBu', vmin=0, vmax=1)
# Blue areas = Democratic, Red areas = Republican ✓

# Partisan swing map
gdf.plot(column='swing', cmap='RdBu', vmin=-0.2, vmax=0.2)
# Blue areas = Democratic shift, Red areas = Republican shift ✓
```

### Incorrect Usage (Don't Do This!)

```python
# WRONG - colors are backwards!
gdf.plot(column='D_share', cmap='RdBu_r', vmin=0, vmax=1)
# Blue areas = Republican ✗, Red areas = Democratic ✗
```

## How to Remember

Think of it this way:
- **RdBu** = "Red (low/Rep) to Blue (high/Dem)" 
- The name goes in the direction: Red→Blue = increasing values
- For D_share, increasing = more Democratic = should be Blue ✓

## Status

✅ **Fixed:** All visualization functions now use correct `RdBu` colormap
- `src/visualize.py` updated (Nov 2025)
- Default parameters corrected
- All map functions use proper political colors

## Verification

To verify your maps have correct colors:
- Democratic-leaning areas (Columbus urban core, Bexley, etc.) should be **blue**
- Republican-leaning areas (rural townships, Canal Winchester, etc.) should be **red**

Franklin County overall leans Democratic (~65% in 2024), so the map should have more blue than red.

