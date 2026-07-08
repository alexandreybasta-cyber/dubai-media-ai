## System Overview

The frontend uses **Tailwind CSS v4** (via `@tailwindcss/postcss`) as its primary styling framework, integrated into a Next.js 16 application. The styling approach combines utility-first CSS with custom design tokens defined in CSS variables, enabling consistent theming across all components.

## Key Files and Configuration

### Core Styling Files
- **`frontend/src/app/globals.css`** — Central stylesheet that imports Tailwind CSS and defines all design tokens via CSS custom properties within an `@theme inline` block
- **`frontend/postcss.config.mjs`** — PostCSS configuration loading `@tailwindcss/postcss` plugin
- **`frontend/package.json`** — Declares `tailwindcss: ^4` and `@tailwindcss/postcss: ^4` as dev dependencies

### Component Library
- **`frontend/src/components/Button.tsx`** — Reusable button component with `primary`/`secondary` variants using design token colors
- **`frontend/src/components/Card.tsx`** — Base card wrapper with consistent border, radius, and padding
- **`frontend/src/components/Sidebar.tsx`** — Fixed navigation sidebar demonstrating layout patterns and active state styling

## Architecture and Conventions

### Design Token System

Custom design tokens are defined in `globals.css` using CSS custom properties mapped to Tailwind's `@theme inline` directive:

```css
@theme inline {
  --color-primary-50: #fff7ed;
  --color-primary-100: #ffedd5;
  /* ... through primary-900 */
  --color-primary-500: #f97316;  /* Orange brand color */
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}
```

This enables usage of semantic color classes like `bg-primary-500`, `text-primary-700`, `focus:ring-primary-500` throughout the codebase.

### Typography

- **Sans-serif**: Geist font family (loaded via `next/font/google`)
- **Monospace**: Geist Mono for code/technical content
- Font variables are exposed as CSS custom properties (`--font-geist-sans`, `--font-geist-mono`) and applied at the `<html>` level

### Color Palette

The primary color scale is orange-based (`#f97316` at 500), providing warm accent tones. Neutral grays from Tailwind's default palette handle backgrounds, borders, and text hierarchy:
- Backgrounds: `bg-white`, `bg-gray-50`
- Borders: `border-gray-200`, `border-gray-300`
- Text: `text-gray-900` (headings), `text-gray-700` (body), `text-gray-500` (muted)

### Component Styling Patterns

1. **Base + Variant Pattern**: Components like `Button` define a base utility string and merge variant-specific utilities:
   ```tsx
   const base = "inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors";
   const variants = {
     primary: "bg-primary-500 text-white hover:bg-primary-600",
     secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
   };
   ```

2. **Consistent Spacing Scale**: Components use Tailwind's spacing scale consistently:
   - Padding: `p-6` (24px) for cards, `px-4 py-2.5` for buttons/inputs
   - Gaps: `gap-2`, `gap-3` for flex/grid layouts
   - Margins: `mb-1`, `mb-2`, `mt-4` for form element spacing

3. **Border Radius Convention**: 
   - Cards/containers: `rounded-xl` (12px)
   - Buttons/inputs: `rounded-lg` (8px)
   - Small elements: `rounded-md` (6px), `rounded-full` for avatars/badges

4. **Focus Ring Standardization**: All interactive elements use `focus:ring-2 focus:ring-primary-500 focus:ring-offset-2` or `focus:ring-primary-500` for accessible focus states

5. **Form Input Styling**: Inputs follow a consistent pattern:
   ```
   w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm
   text-gray-900 placeholder:text-gray-500
   focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none
   ```

### Layout Architecture

- **Fixed Sidebar**: 256px wide (`w-64`), fixed position with `ml-64` offset on main content
- **Main Content Area**: `flex-1 ml-64 bg-gray-50 min-h-screen` with `p-8` internal padding
- **Page Structure**: Each page wraps content in standard containers; no additional layout wrappers needed beyond root layout

### State-Based Styling

Components use conditional class strings for interactive states:
- Active navigation: `bg-primary-50 text-primary-700` vs inactive `text-gray-600 hover:bg-gray-50`
- Drag-over states: `border-primary-400 bg-primary-50 scale-[1.01]`
- Disabled states: `disabled:opacity-50 disabled:cursor-not-allowed`

### Icon Integration

Icons come from `@heroicons/react` (v2.2.0), used at standard sizes:
- Navigation icons: `w-5 h-5`
- Inline icons: `w-4 h-4`, `w-5 h-5`
- Decorative/large icons: `w-8 h-8`, `w-16 h-16`

## Rules Developers Should Follow

1. **Use design tokens exclusively**: Reference colors via `primary-{shade}` classes, never hardcode hex values in component JSX
2. **Leverage existing components**: Use `Button`, `Card`, and `Sidebar` before creating new styled wrappers
3. **Maintain consistent spacing**: Stick to Tailwind's spacing scale; avoid arbitrary values unless absolutely necessary
4. **Apply focus rings**: All interactive elements must include `focus:ring-2 focus:ring-primary-500` for accessibility
5. **Follow the border radius hierarchy**: `rounded-xl` for cards, `rounded-lg` for inputs/buttons, `rounded-md` for small elements
6. **Use semantic text colors**: `text-gray-900` for headings, `text-gray-700` for body, `text-gray-500` for muted/helper text
7. **Keep component styles inline**: Avoid extracting CSS classes into separate files; use template literals for conditional class merging
8. **Ensure readable form inputs**: The global CSS override ensures `input`, `textarea`, `select` always have dark text (`#1f2937`) regardless of background