# Corvallis School District 509J — Website Redesign

A complete, production-ready school district website built with plain HTML, CSS, and vanilla JavaScript. No frameworks, no build tools, no dependencies to maintain. Hosted free on GitHub Pages.

**Live site:** [mr-mcateer.github.io/csd509j-redesign](https://mr-mcateer.github.io/csd509j-redesign/)

---

## Quick Start

1. Clone or download this repository
2. Open `index.html` in a browser — it works immediately (no build step)
3. Edit the HTML files directly to update content
4. Push to GitHub to deploy via GitHub Pages

---

## What's Included

| Page | File | What It Contains |
|------|------|------------------|
| **Homepage** | `index.html` | Hero, quick links, stats, news cards, strategic goals |
| **About** | `about/index.html` | District info, leadership, strategic plan, equity, budget, facilities |
| **Schools** | `schools/index.html` | 13 school profiles with filter tabs (Elementary/Middle/High/Charter/K-8) |
| **Families** | `families/index.html` | Enrollment, transportation, menus, safety, special education |
| **Community** | `community/index.html` | School board, employment, calendar, facility use |
| **Staff** | `staff/index.html` | ClassLink, contracts, benefits, IT resources |
| **Departments** | `departments/index.html` | Department directory with contact info |
| **Contact** | `contact/index.html` | Contact directory by department |
| **News** | `news/index.html` | News articles with images |
| **How It Was Built** | `how-it-was-built/index.html` | Behind-the-scenes story of how AI built this site |

---

## File Structure

```
csd509j-redesign/
├── index.html                  ← Homepage
├── README.md                   ← You are here
├── CUSTOMIZATION-GUIDE.md      ← Step-by-step editing instructions
│
├── about/index.html            ← About the District
├── schools/index.html          ← School Directory (with filter JS)
├── families/index.html         ← For Families
├── community/index.html        ← Community Resources
├── staff/index.html            ← Staff Resources
├── departments/index.html      ← Department Directory
├── contact/index.html          ← Contact Information
├── news/index.html             ← News & Updates
├── how-it-was-built/index.html ← How This Site Was Built
│
├── css/
│   └── styles.css              ← All styling (1,836 lines, 32 components)
│
├── js/
│   ├── nav.js                  ← Navigation, mobile drawer, breadcrumbs
│   ├── search.js               ← Cmd+K search overlay with static index
│   └── main.js                 ← Scroll reveal, counters, accordions
│
├── data/                       ← Reference data (not loaded by the site)
│   ├── district.json           ← District name, address, phone, stats
│   ├── schools.json            ← All 13 schools with details
│   ├── departments.json        ← Department names, phones, descriptions
│   └── navigation.json         ← Menu structure and quick links
│
└── images/
    ├── csd-logo-dark.svg       ← Logo for light backgrounds
    ├── csd-logo-white.svg      ← Logo for dark backgrounds
    ├── hero-community.jpg      ← Homepage hero background
    ├── community-meeting.jpg   ← Community/budget stories
    ├── families-walking.jpg    ← Enrollment/families stories
    ├── school-hallway.jpg      ← General education imagery
    ├── staff-meeting.jpg       ← Staff page photo break
    ├── heroes/
    │   ├── community.jpg       ← Inner page hero + About photo break
    │   └── oregon.jpg          ← About page photo break
    ├── news/
    │   ├── students.jpg        ← News card image
    │   ├── food.jpg            ← News card image
    │   ├── hands-on.jpg        ← News card image
    │   └── bus.jpg             ← News card image
    └── schools/
        ├── elementary.jpg      ← Schools page photo break
        ├── high-school.jpg     ← (available for use)
        └── school-building.jpg ← Homepage + page hero CSS background
```

---

## Before You Deploy: What to Change

These are the items a district administrator **must update** before going live. See `CUSTOMIZATION-GUIDE.md` for detailed, line-by-line instructions.

### Critical (Must Change)

| What | Where | Why |
|------|-------|-----|
| **District name** | Every HTML file `<title>`, nav logo, footer | Currently says "Corvallis School District 509J" |
| **Phone number** | `(541) 757-5811` appears in utility bar, footer, and contact pages | Every page header and footer |
| **Address** | `1555 SW 35th Street, Corvallis, OR 97333` | Footer on every page |
| **School names & details** | `schools/index.html` | 13 schools with addresses, phones, grades, websites |
| **Superintendent name** | `about/index.html`, `data/district.json` | Currently "Ryan Noss" |
| **Board member names** | `about/index.html`, `community/index.html` | 7 board members listed |
| **School website URLs** | `schools/index.html` | Links like `https://adams.csd509j.net` |
| **Social media links** | Footer on every page | Facebook, Instagram, YouTube URLs |
| **Logo SVG files** | `images/csd-logo-dark.svg`, `images/csd-logo-white.svg` | Replace with your district logo |
| **Copyright year** | Footer on every page | Currently `2026` |

### Important (Should Change)

| What | Where | Why |
|------|-------|-----|
| **Stats numbers** | `index.html` (homepage stats bar) | 5,859 students, 917 staff, etc. |
| **News articles** | `news/index.html` | Placeholder stories about budget, enrollment, etc. |
| **Department info** | `departments/index.html`, `contact/index.html` | Phone numbers and descriptions |
| **Strategic goals** | `about/index.html` | 4 goals specific to CSD 509J |
| **Consolidation notices** | `schools/index.html`, `about/index.html` | Cheldelin consolidation warning |
| **Search index** | `js/search.js` | 52 entries that power Cmd+K search |
| **Photos** | `images/` directory | Replace with your own school photos |
| **Meta descriptions** | `<meta name="description">` in every HTML file | SEO descriptions mention Corvallis |
| **Canonical URLs** | `<link rel="canonical">` in every HTML file | Points to `mr-mcateer.github.io` |

---

## How the CSS Design System Works

The entire site is styled from a single file: `css/styles.css`. It uses CSS custom properties (variables) defined at the top, so changing the look of the whole site is straightforward.

### Color Palette

To change the district colors, edit these variables in `styles.css` (lines 10-17):

```css
:root {
  --navy: #003a6b;       /* Dark blue — nav, footer, dark sections */
  --blue: #004a8d;       /* Primary blue — links, buttons, accents */
  --gold: #FCB644;        /* Accent gold — highlights, callouts */
}
```

Change these three values and the entire site updates — every button, link, heading accent, and section background.

### Typography

Three font stacks (line 42-44):

```css
--font-display: 'Inter', sans-serif;   /* Headings */
--font-body: 'Inter', sans-serif;      /* Body text */
--font-mono: 'JetBrains Mono', mono;   /* Labels, data, tags */
```

### Component Classes

The CSS provides 32 reusable component classes. The most commonly used:

| Class | What It Does |
|-------|-------------|
| `.section--light` | White background section |
| `.section--gray` | Light gray background section |
| `.section--dark` | Navy background with white text |
| `.card` | White card with border and hover shadow |
| `.callout` | Blue-bordered info box |
| `.callout--warning` | Orange-bordered warning box |
| `.stats-bar` | Horizontal row of large numbers |
| `.grid--3` | 3-column card grid |
| `.grid--4` | 4-column card grid |
| `.grid--auto` | Auto-fill grid (responsive columns) |
| `.accordion` | Expandable content sections |
| `.btn--primary` | Blue filled button |
| `.photo-break` | Full-width image divider between sections |
| `.reveal` | Fade-in animation on scroll |

---

## How the JavaScript Works

All JavaScript is vanilla — no jQuery, no React, no build step. Three files, zero dependencies.

### nav.js (171 lines)
- **Mobile hamburger menu** — opens/closes the slide-out drawer
- **Active link highlighting** — detects current page and highlights nav link
- **Breadcrumb generation** — auto-builds "Home / About / ..." trail from URL
- **Keyboard support** — Escape key closes mobile menu

### search.js (201 lines)
- **Cmd+K / Ctrl+K** opens the search overlay
- **Static search index** — 52 entries (schools, departments, pages)
- **Debounced input** — 120ms delay prevents excessive re-rendering
- **Highlighted matches** — search terms highlighted in results

> **To update search:** Edit the `SEARCH_INDEX` array at the top of `search.js`. Each entry needs `name`, `section`, and `href`.

### main.js (192 lines)
- **Scroll reveal** — elements fade in as you scroll (uses IntersectionObserver)
- **Counter animation** — stats numbers count up from zero
- **Accordion** — click-to-expand content sections
- **Reduced motion** — respects `prefers-reduced-motion` accessibility setting

---

## Hosting & Deployment

The site is currently deployed via **GitHub Pages** at no cost.

### How It Works
1. Push changes to the `main` branch
2. GitHub Actions automatically deploys within ~30 seconds
3. The site is live at `https://[username].github.io/[repo-name]/`

### To Deploy on Your Own GitHub
1. Fork or copy this repository
2. Go to **Settings > Pages** in your GitHub repo
3. Set Source to "Deploy from a branch" → `main` → `/ (root)`
4. Your site will be live at `https://[your-org].github.io/[repo-name]/`

### Custom Domain (Optional)
To use a domain like `www.yourdistrict.org`:
1. Add a `CNAME` file to the repo root containing: `www.yourdistrict.org`
2. In your DNS provider, add a CNAME record pointing to `[your-org].github.io`
3. Enable "Enforce HTTPS" in GitHub Pages settings

### Alternative Hosting
Since this is just static HTML/CSS/JS, it works on any web server:
- **Netlify** — drag and drop the folder
- **Cloudflare Pages** — connect your GitHub repo
- **Any web server** — upload the files via FTP/SFTP

---

## Accessibility

The site targets **WCAG 2.1 AA** compliance:

- Skip-to-main-content link on every page
- Semantic HTML landmarks (`<nav>`, `<main>`, `<footer>`, `<section>`)
- ARIA labels on all interactive regions
- Full keyboard navigation (tab, enter, escape)
- Minimum 4.5:1 color contrast ratios
- `prefers-reduced-motion` respected — all animations disabled
- Print stylesheet included

---

## Browser Support

Tested and working in:
- Chrome / Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

The site uses no bleeding-edge features. It works in any browser released after 2018.

---

## Credits

Designed and built by **Andy McAteer** (CTE Instructor, Crescent Valley High School) using [Claude Code](https://claude.ai) by Anthropic.

All photographs sourced from [Unsplash](https://unsplash.com) under the Unsplash License (free for commercial use).

---

## License

This website template is provided as an open educational resource. School districts are welcome to fork, modify, and deploy it for their own use.
