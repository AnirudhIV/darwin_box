// Ported from charting.py - same validated categorical palette, so the
// Streamlit (Plotly) and React (Recharts) frontends visually match. Dark
// variants are the same eight hues re-stepped for the dark surface, not a
// separate palette (per the dataviz skill's palette reference).
export const CATEGORICAL = [
  '#2a78d6',
  '#eb6834',
  '#1baf7a',
  '#eda100',
  '#e87ba4',
  '#008300',
  '#4a3aa7',
  '#e34948',
]
export const CATEGORICAL_DARK = [
  '#3987e5',
  '#d95926',
  '#199e70',
  '#c98500',
  '#d55181',
  '#008300',
  '#9085e9',
  '#e66767',
]

export const SEQUENTIAL_BLUE = '#2a78d6'
export const SEQUENTIAL_BLUE_DARK = '#3987e5'
export const GRIDLINE = '#e1e0d9'
export const GRIDLINE_DARK = '#2c2c2a'
export const AXIS = '#c3c2b7'
export const AXIS_DARK = '#383835'
export const MUTED = '#898781' // same in both modes
export const INK = '#0b0b0b'
export const INK_DARK = '#ffffff'
export const SURFACE = '#fcfcfb'
export const SURFACE_DARK = '#1a1a19'

export function chartColors(theme: 'light' | 'dark') {
  return theme === 'dark'
    ? {
        categorical: CATEGORICAL_DARK,
        sequentialBlue: SEQUENTIAL_BLUE_DARK,
        gridline: GRIDLINE_DARK,
        axis: AXIS_DARK,
        muted: MUTED,
        ink: INK_DARK,
        surface: SURFACE_DARK,
      }
    : {
        categorical: CATEGORICAL,
        sequentialBlue: SEQUENTIAL_BLUE,
        gridline: GRIDLINE,
        axis: AXIS,
        muted: MUTED,
        ink: INK,
        surface: SURFACE,
      }
}
