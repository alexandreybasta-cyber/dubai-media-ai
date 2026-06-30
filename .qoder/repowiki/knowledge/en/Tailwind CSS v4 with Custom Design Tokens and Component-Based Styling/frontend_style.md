## Styling System

The Dubai Media AI Dashboard uses **Tailwind CSS v4** as its primary styling framework, configured via the `@tailwindcss/postcss` plugin. The project leverages Tailwind's new v4 configuration approach using CSS-based theme definitions rather than a JavaScript config file.

### Core Technology Stack

- **Framework**: Next.js 16.2.9 with React 19
- **CSS Framework**: Tailwind CSS v4 (via `@tailwindcss/postcss`)
- **Icon Library**: Heroicons v2 (`@heroicons/react`) for consistent iconography
- **Font System**: Geist Sans + Geist Mono (Google Fonts via `next/font/google`)
- **Charting**: Recharts v3.9.0 for data visualization

### Design Token Architecture

Design tokens are defined in `globals.css` using CSS custom properties within a `@theme inline` block:

**Color Palette:**
- **Primary Scale**: Orange-based palette (`primary-50` through `primary-900`) mapped to hex values from `#fff7ed` to `#7c2d12`, with `primary-500` (#f97316) as the brand accent color
- **Semantic Colors**: Background/foreground pairs supporting both light and dark modes via `prefers-color-scheme: dark` media query
- **Utility Colors**: Tailwind's built-in gray scale (`gray-50` through `gray-900`) used extensively for UI surfaces, borders, and text hierarchy

**Typography:**
- **Sans-serif**: Geist (variable `--font-geist-sans`)
- **Monospace**: Geist Mono (variable `--font-geist-mono`)
- **Fallback**: Arial, Helvetica, sans-serif

### Component Library Pattern

The project implements a **minimal custom component library** with two reusable primitives:

1. **Button** (`components/Button.tsx`): Variant-based API (`primary` | `secondary`) with consistent padding, rounded corners, focus rings, and disabled states
2. **Card** (`components/Card.tsx`): White background, rounded-xl corners, subtle border (`border-gray-200`), and standard padding

These components use **composition over configuration** — they accept a `className` prop for overrides while providing sensible defaults.

### Layout Strategy

The root layout (`layout.tsx`) establishes a **fixed sidebar + fluid main content** pattern:

- **Sidebar**: Fixed position, 64rem width (`w-64`), white background with right border
- **Main Content**: Flex-grow container with left margin offset (`ml-64`), light gray background (`bg-gray-50`), and generous padding (`p-8`)
- **Full-height**: Both `html` and `body` set to `min-h-full` with flexbox for proper viewport coverage

### Responsive Approach

The application uses Tailwind's mobile-first responsive utilities sparingly but consistently:
- Grid layouts switch from single-column to multi-column at breakpoints (`grid-cols-1 lg:grid-cols-3`)
- Feature cards stack vertically on mobile, expand horizontally on large screens
- No explicit breakpoint customization found — relies on Tailwind defaults

### Styling Conventions

**Class Composition Patterns:**
- Components use template literals for conditional class merging: `` `${base} ${variants[variant]} ${className}` ``
- State-based styling (active/hover) uses ternary expressions within className strings
- Transition effects applied consistently: `transition-colors` for interactive elements, `transition-all` for card hover states

**Visual Hierarchy:**
- Headings: `text-lg font-semibold` or `text-4xl font-bold` for hero sections
- Body text: `text-sm text-gray-500` for descriptions, `text-xs` for metadata/captions
- Interactive links: Orange accent color (`text-orange-600 hover:text-orange-700`)

**Spacing System:**
- Consistent use of Tailwind's spacing scale: `p-6`, `px-4 py-2.5`, `gap-3`, `space-y-1`
- Section margins: `mb-12` for major divisions, `mt-4` for internal spacing

### Dark Mode Support

Basic dark mode is implemented via CSS media query (`prefers-color-scheme: dark`), swapping background/foreground colors. However, no explicit dark mode toggle or `dark:` variant usage was found in components, suggesting this is currently a system-preference-only feature.

### Developer Guidelines

1. **Use design tokens**: Reference `primary-*` colors instead of hardcoded hex values
2. **Component first**: Use `<Button>` and `<Card>` primitives before writing raw divs with Tailwind classes
3. **Consistent spacing**: Follow the established padding/scale patterns (p-6 for cards, px-4 py-2.5 for buttons)
4. **State styling**: Apply `focus:ring-2 focus:ring-offset-2` for accessibility on interactive elements
5. **Icon integration**: Use Heroicons outline variants at consistent sizes (w-5 h-5 for nav, w-6 h-6 for features)
6. **Border strategy**: Subtle borders (`border-gray-200`) for card separation, avoid heavy shadows
