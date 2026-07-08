---
kind: frontend_style
name: Tailwind CSS v4 with Custom Design Tokens and Component-Based Styling
category: frontend_style
scope:
    - '**'
source_files:
    - frontend/src/app/globals.css
    - frontend/postcss.config.mjs
    - frontend/package.json
    - frontend/src/app/layout.tsx
    - frontend/src/components/Button.tsx
    - frontend/src/components/Card.tsx
    - frontend/src/components/Sidebar.tsx
---

## System Overview

The frontend uses **Tailwind CSS v4** as its primary styling framework, integrated with Next.js 16 via the `@tailwindcss/postcss` plugin. The styling approach combines utility-first CSS with custom design tokens defined in CSS custom properties, enabling consistent theming across the application.

## Key Files and Configuration

### Core Styling Files
- **`frontend/src/app/globals.css`** — Global stylesheet that imports Tailwind CSS v4 (`@import "tailwindcss"`) and defines the design token system using CSS custom properties within an `@theme inline` block.
- **`frontend/postcss.config.mjs`** — PostCSS configuration that registers `@tailwindcss/postcss` as the sole plugin.
- **`frontend/package.json`** — Declares `tailwindcss: ^4` and `@tailwindcss/postcss: ^4` as dev dependencies.

### Design Token Definitions (in `globals.css`)
The `@theme inline` block defines:
- **Color palette**: A complete orange-based primary color scale from `--color-primary-50` (#fff7ed) through `--color-primary-900` (#7c2d12), mapped to Tailwind's `primary-*` utility classes.
- **Semantic colors**: `--color-background` and `--color-foreground` for theme-aware body styling.
- **Typography**: `--font-sans` and `--font-mono` referencing Geist font families loaded via `next/font/google`.

### Font Loading
Fonts are configured in **`frontend/src/app/layout.tsx`** using Next.js font optimization:
```tsx
const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
```
These variables are applied to the `<html>` element's `className`, making them available as CSS custom properties throughout the app.

## Architecture and Conventions

### Component Library Pattern
Reusable UI components live in **`frontend/src/components/`** and follow a consistent pattern:
- **`Button.tsx`** — Supports `primary` and `secondary` variants using Tailwind utility strings composed at runtime. Primary uses `bg-primary-500 text-white hover:bg-primary-600`; secondary uses bordered neutral styling.
- **`Card.tsx`** — Provides a standard card container with `bg-white rounded-xl border border-gray-200 p-6`.
- **`Sidebar.tsx`** — Fixed-position navigation sidebar (`w-64 bg-white border-r border-gray-200`) with active state highlighting using `bg-primary-50 text-primary-700`.

### Styling Methodology
1. **Utility-first with composition**: All components use inline Tailwind utility classes. Complex class strings are composed using template literals with conditional logic (e.g., active/inactive states in Sidebar).
2. **Design token usage**: The custom `primary-*` color scale is used consistently for brand accents (orange #f97316 as primary-500). Components reference these via standard Tailwind class names like `text-primary-500`, `bg-primary-50`, `hover:bg-primary-600`.
3. **Neutral palette**: Gray scale utilities (`gray-50` through `gray-900`) provide backgrounds, borders, and text hierarchy.
4. **Semantic color coding**: Feature cards use distinct color schemes (blue for Archive, orange for RFP Creator, emerald for Evaluator) via inline style objects passed as props.

### Layout Structure
- **Root layout** (`layout.tsx`) establishes a two-column layout: fixed sidebar (`ml-64` offset on main content) with `bg-gray-50` page background.
- Pages wrap content in max-width containers (`max-w-6xl mx-auto`) for readability.
- Consistent spacing: `p-8` padding on main content, `gap-6` for grid layouts.

### Accessibility and UX Patterns
- Focus rings: Buttons include `focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500`.
- Disabled states: `disabled:opacity-50 disabled:cursor-not-allowed`.
- Transition effects: `transition-colors` or `transition-all` on interactive elements.
- Form input overrides: Global CSS ensures readable text color (`#1f2937`) and placeholder color (`#6b7280`) for inputs, textareas, and selects.

## Rules Developers Should Follow

1. **Use design tokens via Tailwind classes**: Reference colors using `primary-{shade}` (e.g., `text-primary-600`, `bg-primary-50`) rather than hardcoded hex values. The primary scale is orange-based.
2. **Compose component variants with utility strings**: When building reusable components, define variant styles as concatenated Tailwind utility strings (see `Button.tsx` pattern).
3. **Maintain gray scale hierarchy**: Use `gray-50` for subtle backgrounds, `gray-200` for borders, `gray-500` for secondary text, `gray-900` for primary headings.
4. **Apply consistent spacing**: Use `p-6` for card padding, `gap-6` for grid gaps, `space-y-1` or `space-y-1.5` for vertical lists.
5. **Border radius convention**: Use `rounded-lg` for buttons and small elements, `rounded-xl` for cards and larger containers, `rounded-full` for badges/pills.
6. **Font usage**: Body text uses Geist Sans (via `--font-geist-sans`). Monospace contexts use Geist Mono. Avoid overriding font families unless necessary.
7. **Responsive strategy**: The current codebase uses mobile-first defaults with explicit breakpoints only where needed (e.g., `md:grid-cols-3`, `lg:grid-cols-3`). Follow this pattern for new responsive layouts.
8. **No dark mode toggle implemented**: While `globals.css` contains a `prefers-color-scheme: dark` media query in one section, the active theme definition does not include dark mode overrides. Assume light-mode-only unless explicitly extended.
