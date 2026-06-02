---
name: Finanza Fluida
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#ccc3d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#958da1'
  outline-variant: '#4a4455'
  surface-tint: '#d3bbff'
  primary: '#d3bbff'
  on-primary: '#3f008d'
  primary-container: '#6d28d9'
  on-primary-container: '#dac5ff'
  inverse-primary: '#7331df'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#006544'
  on-tertiary-container: '#58e7ab'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ebddff'
  primary-fixed-dim: '#d3bbff'
  on-primary-fixed: '#250059'
  on-primary-fixed-variant: '#5b00c5'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  currency-display:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-margin: 20px
  gutter: 16px
---

## Brand & Style
The design system is engineered for a personal finance assistant that balances institutional trust with cutting-edge agility. Targeted at a tech-savvy demographic, the visual language moves away from traditional "bank green" toward a high-fidelity "Digital Wealth" aesthetic.

The style is **Modern Corporate with Glassmorphic accents**. It utilizes a sophisticated dark-mode-first foundation where depth is communicated through translucent layers and subtle atmospheric glows rather than heavy physical metaphors. The emotional response should be one of "controlled clarity"—making complex financial data feel breathable, manageable, and forward-looking.

## Colors
The palette is rooted in **Deep Violet** and **Vibrant Blue**, creating a "Cyber-Finance" atmosphere that distinguishes the app from stagnant traditional banking interfaces.

- **Primary (#6D28D9):** Used for main actions, active states, and brand-heavy moments.
- **Secondary (#3B82F6):** Used for informational accents, charts, and secondary call-to-actions.
- **Surface & Background:** A deep navy-black (#0F172A) serves as the canvas, with (#1E293B) used for elevated card surfaces to maintain high contrast with text.
- **Success/Positive (#10B981):** A crisp emerald for income and positive market trends (ARS growth).
- **Semantic Accents:** Use subtle background gradients (Primary to Secondary at 15% opacity) to create "pools of light" behind key financial summaries.

## Typography
The system uses **Inter** for its exceptional legibility in data-dense environments. For technical and numerical data, **Geist** is introduced to provide a precise, monospaced feel that aligns with the tech-focused theme.

**Localization (Argentina):** 
- Ensure currency formatting (ARS) uses `tabularNums` to keep decimals aligned in lists.
- Headlines should account for longer Spanish word lengths (e.g., "Presupuesto" vs "Budget") by maintaining generous line height.
- All labels and calls-to-action must use Argentinian Spanish conventions (voseo) where applicable for an approachable local feel.

## Layout & Spacing
This design system follows a **Mobile-First Fluid Grid**. While the app is web-based, it mimics native behavior with a focus on thumb-reach zones and vertical scrolling.

- **Grid:** A 4-column layout for mobile, scaling to 12 columns for desktop.
- **Rhythm:** An 8px linear scale is used for all spatial relationships.
- **Max Width:** For desktop viewing, the main content area is capped at 1200px to maintain readability of financial tables.
- **Touch Targets:** Minimum 44x44px for all interactive elements to ensure accessibility on mobile devices.

## Elevation & Depth
Depth is created through **Glassmorphism and Tonal layering** rather than traditional drop shadows.

1.  **Level 0 (Base):** Deepest layer (#0F172A).
2.  **Level 1 (Cards):** Surface color (#1E293B) with a 1px subtle stroke (#334155).
3.  **Level 2 (Glass Accents):** Semi-transparent surfaces (Background Blur: 12px, Opacity: 60%) used for floating navigation bars or featured "Total Balance" cards.
4.  **Shadows:** When used, shadows are "Ambient Glows"—large blur radii (24px+) with low opacity (10-15%) using the primary violet or secondary blue color to suggest a light source from the content itself.

## Shapes
The shape language is defined by **High-Radius Geometry**. This softens the "technical" feel of the app, making it feel more like a lifestyle companion than a spreadsheet.

- **Standard Elements:** 0.5rem (8px) for input fields and small buttons.
- **Containers/Cards:** 1rem (16px) for the main structural containers.
- **Featured Surfaces:** 1.5rem (24px) for high-impact glassmorphic cards and modal bottom sheets.
- **Icons:** Encapsulated in rounded-full (pill) containers when used as category markers (e.g., Gastos, Ahorros).

## Components

### Buttons
- **Primary:** Solid #6D28D9 with white text. High roundedness (pill-style). Subtle 10% brightness increase on hover/touch.
- **Glass:** Transparent background with a white 10% opacity fill and 20px backdrop-blur. Used for secondary actions on top of gradients.

### Cards
- Financial cards should feature a subtle gradient border (Linear: Primary to Secondary). 
- Inner padding should be a consistent `lg` (24px) to give data room to breathe.

### Input Fields
- Dark backgrounds (#0F172A) with a soft border (#334155). On focus, the border transitions to Primary Violet with a subtle outer glow.
- In Argentina, ensure the currency prefix `$` is always present in amount inputs.

### Chips & Tags
- Used for transaction categories (e.g., "Comida", "Transporte"). Use low-saturation versions of the accent colors with high-contrast text.

### Progress Bars
- Smooth, rounded tracks. For savings goals, use a gradient fill from Secondary Blue to Tertiary Emerald to visually represent "growth."