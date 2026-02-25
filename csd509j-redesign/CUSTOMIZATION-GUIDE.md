# Customization Guide — CSD 509J Website Template

This guide walks you through every change needed to make this website yours. No coding experience required — you just need a text editor and the ability to find-and-replace.

**Estimated time:** 1-2 hours for a basic deployment. Half a day for full customization.

---

## Table of Contents

1. [Tools You'll Need](#1-tools-you-ll-need)
2. [Global Find-and-Replace (30 minutes)](#2-global-find-and-replace)
3. [Update the Logo](#3-update-the-logo)
4. [Update the Homepage](#4-update-the-homepage)
5. [Update School Profiles](#5-update-school-profiles)
6. [Update News Articles](#6-update-news-articles)
7. [Update Department Info](#7-update-department-info)
8. [Update the Search Index](#8-update-the-search-index)
9. [Change the Color Scheme](#9-change-the-color-scheme)
10. [Replace Photos](#10-replace-photos)
11. [Set Up Hosting](#11-set-up-hosting)
12. [Common Tasks](#12-common-tasks)

---

## 1. Tools You'll Need

- **A text editor.** [Visual Studio Code](https://code.visualstudio.com/) (free) is recommended. It has built-in find-and-replace across files.
- **A browser.** Chrome, Firefox, or Safari to preview changes.
- **A GitHub account.** Free at [github.com](https://github.com) — needed for free hosting.

That's it. No special software, no command line required.

---

## 2. Global Find-and-Replace

Open the entire `csd509j-redesign` folder in VS Code, then use **Edit > Replace in Files** (Cmd+Shift+H on Mac, Ctrl+Shift+H on Windows). Make these replacements across ALL files:

### District Identity

| Find | Replace With | Files Affected |
|------|-------------|----------------|
| `Corvallis School District 509J` | Your district's full name | ~20 matches across all pages |
| `Corvallis School District` | Your district's name (without number) | ~30 matches |
| `CSD 509J` | Your abbreviation | ~10 matches |
| `509J` | Your district number | ~10 matches (nav logo) |
| `Corvallis` | Your city name | ~50+ matches (review each — some are in addresses) |

### Contact Information

| Find | Replace With | Files Affected |
|------|-------------|----------------|
| `(541) 757-5811` | Your main phone number | Every page (utility bar + footer) |
| `1555 SW 35th Street` | Your street address | Footer on every page |
| `Corvallis, OR 97333` | Your city, state, zip | Footer on every page |
| `tel:+15417575811` | `tel:+1XXXXXXXXXX` (your number) | Every page |

### Social Media

In the footer of every HTML file, find and replace these URLs:

| Find | Replace With |
|------|-------------|
| `https://www.facebook.com/CorvallisSD` | Your Facebook page URL |
| `https://www.instagram.com/corvallissd/` | Your Instagram URL |
| `https://www.youtube.com/@CorvallisSchoolDistrict` | Your YouTube URL |

If you don't have one of these accounts, delete the entire `<a>...</a>` block for that platform in the footer.

### Website References

| Find | Replace With |
|------|-------------|
| `https://www.csd509j.net` | Your official district website URL |
| `mr-mcateer.github.io/csd509j-redesign` | Your deployment URL |
| `csd509j.net` | Your domain |

---

## 3. Update the Logo

Replace these two files with your district's logo:

- `images/csd-logo-dark.svg` — Used in the navigation bar (dark text on light background)
- `images/csd-logo-white.svg` — Used in the footer (white on dark background)

**Requirements:**
- SVG format is ideal (scales to any size, tiny file)
- If you only have a PNG, that works too — just rename it to match
- Keep the filename the same, or update the `<img src="...">` in every HTML file's nav and footer

**Where the logo appears in HTML** (same in every page):
```html
<!-- In the <nav> -->
<img src="../images/csd-logo-dark.svg" alt="Your District Name" class="site-nav__logo-img">
<span>509J</span>  <!-- Change this to your district number -->

<!-- In the <footer> -->
<img src="../images/csd-logo-white.svg" alt="Your District Name" class="footer__logo">
```

---

## 4. Update the Homepage

Open `index.html` (the file in the root folder, not inside a subfolder).

### Hero Section (the big banner at the top)

Find the `<!-- Hero Section -->` comment. Update:

```html
<p class="hero__eyebrow">Corvallis School District 509J</p>
<!-- Change to your district name -->

<h1 class="reveal">Every Student. Every Day.</h1>
<!-- Change to your motto/tagline -->

<p class="hero__sub">...</p>
<!-- Change to your introductory text -->
```

### Stats Bar

Find the `<!-- Stats Bar -->` section. Each stat looks like:

```html
<div class="stat">
  <div class="stat__number" data-counter="5859">0</div>
  <div class="stat__label">Students Enrolled</div>
</div>
```

Change `data-counter="5859"` to your number. The counter will animate from 0 to that number on scroll. Update the label text to match.

### Superintendent Quote

Find the `<!-- Superintendent Quote -->` section and update the name, title, and quote text.

### News Cards

The homepage shows 4 news stories. Each one looks like:

```html
<article class="card news-card reveal">
  <img src="images/news/students.jpg" ...>
  <div class="card__body">
    <p class="news-card__date">February 12, 2026</p>
    <h3 class="card__title">Article Title Here</h3>
    <p class="card__desc">Article summary here.</p>
  </div>
</article>
```

Replace the title, date, summary, and image for each card.

---

## 5. Update School Profiles

Open `schools/index.html`. Each school is an `<article>` element:

```html
<article class="card school-card reveal" data-type="elementary" id="adams">
  <div class="card__body">
    <span class="school-card__type">Elementary</span>
    <h3 class="card__title">Adams Elementary</h3>
    <p class="school-card__grades">Grades K-5</p>
    <p class="card__desc">1615 SW 35th St, Corvallis, OR 97333</p>
    <p class="card__meta">(541) 757-5961</p>
    <p class="card__desc" style="...">Dual Language Immersion</p>
    <a href="https://adams.csd509j.net" class="school-card__link">
      Visit school website →
    </a>
  </div>
</article>
```

**For each school, update:**
1. `data-type="elementary"` — must be `elementary`, `middle`, `high`, `charter`, or `k8` (controls the filter)
2. `id="adams"` — a unique short name (used for anchor links)
3. The school name, grades, address, phone, programs, and website URL

**To add a new school:** Copy an entire `<article>...</article>` block and paste it in the right position. Update all the details.

**To remove a school:** Delete the entire `<article>...</article>` block.

**The Cheldelin consolidation notice** (the yellow warning box) can be removed by deleting the `<div class="callout callout--warning ...">...</div>` block.

---

## 6. Update News Articles

Open `news/index.html`. Each article is a card. To add a new story:

```html
<article class="card news-card reveal">
  <img src="../images/news/your-photo.jpg" alt="Description of photo"
       class="card__image" loading="lazy" width="400" height="200">
  <div class="card__body">
    <p class="news-card__date">March 15, 2026</p>
    <h3 class="card__title">Your Headline Here</h3>
    <p class="card__desc">A 1-2 sentence summary of the article.</p>
  </div>
</article>
```

Place new articles at the top of the grid (after the `<div class="grid--auto">` line) so they appear first.

---

## 7. Update Department Info

Open `departments/index.html`. Each department is a card:

```html
<article class="card dept-card reveal">
  <div class="card__body">
    <span class="dept-card__icon">💼</span>
    <h3 class="card__title">Business Services</h3>
    <p class="card__desc">Budget, finance, payroll...</p>
    <p class="dept-card__phone">(541) 757-5811</p>
  </div>
</article>
```

Update names, descriptions, and phone numbers. The emoji icons can be changed to any emoji.

Also update the contact page (`contact/index.html`) to match.

---

## 8. Update the Search Index

Open `js/search.js`. At the top is the `SEARCH_INDEX` array:

```javascript
var SEARCH_INDEX = [
  { name: 'About', section: 'District', href: 'about/' },
  { name: 'Adams Elementary', section: 'Schools', href: 'schools/#adams' },
  // ... more entries
];
```

**Each entry has three fields:**
- `name` — what the user types to find it
- `section` — the category label shown in results
- `href` — the page it links to (relative to the site root)

Add, remove, or edit entries to match your district's content. If you add a new school, add a search entry for it here too.

---

## 9. Change the Color Scheme

Open `css/styles.css`. The color palette is defined at the very top (around line 10):

```css
:root {
  --navy: #003a6b;       /* Darkest blue — used for nav, footer, dark sections */
  --blue: #004a8d;       /* Primary blue — links, buttons, active states */
  --gold: #FCB644;        /* Accent color — highlights, special callouts */
}
```

**To match your district's colors:**
1. Change `--navy` to your darkest brand color
2. Change `--blue` to your primary brand color
3. Change `--gold` to your accent/secondary color

Everything else adapts automatically — buttons, links, hover states, section backgrounds, the nav bar, the footer.

**Example for a red/gray district:**
```css
--navy: #7B1113;       /* Dark red */
--blue: #C41E3A;       /* Primary red */
--gold: #E8A317;        /* Gold accent */
```

---

## 10. Replace Photos

All images are in the `images/` directory. To replace one:

1. Add your new image to the same folder
2. Name it the same as the old one (e.g., `hero-community.jpg`), OR
3. Update the `<img src="...">` in the HTML to point to your new filename

**Image size recommendations:**
- Hero/banner images: 1200px wide, JPG, under 500KB
- News card images: 400px wide, JPG, under 100KB
- Photo break images: 1200px wide, JPG, under 300KB

**The two CSS background images** need to be updated in `css/styles.css`:
- Line ~598: `.hero` background → `images/schools/school-building.jpg`
- Line ~667: `.page-hero` background → `images/heroes/community.jpg`

---

## 11. Set Up Hosting

### GitHub Pages (Free — Recommended)

1. Create a GitHub account at [github.com](https://github.com)
2. Create a new repository (name it anything, e.g., `district-website`)
3. Upload all files from the `csd509j-redesign` folder
4. Go to **Settings > Pages**
5. Under "Source," select **Deploy from a branch** > **main** > **/ (root)**
6. Click Save
7. Your site will be live at `https://[your-username].github.io/[repo-name]/` within a minute

### Custom Domain

If your district has a domain (like `www.yourdistrict.org`):

1. In your repo, create a file called `CNAME` containing just: `www.yourdistrict.org`
2. In your DNS provider, add a CNAME record: `www` → `[your-username].github.io`
3. In GitHub Pages settings, type your domain and check "Enforce HTTPS"

---

## 12. Common Tasks

### Add a new page

1. Create a new folder (e.g., `calendar/`)
2. Copy any existing `index.html` as a starting point
3. Keep the `<nav>`, `<footer>`, and `<script>` tags unchanged
4. Replace the `<main>` content with your new content
5. Update the `<title>` and `<meta>` tags in `<head>`

### Change the navigation menu

The navigation is hardcoded in every HTML file (not generated from a file). To add a nav link:

1. Find `<ul class="site-nav__links">` in the page
2. Add a new `<li><a href="../yournewpage/">Page Name</a></li>`
3. Repeat in the mobile nav section (`<nav class="mobile-nav">`)
4. **Do this in every HTML file** — there are 10 pages

### Add a photo break between sections

Insert this HTML between any two `<section>` elements:

```html
<div class="photo-break" aria-hidden="true">
  <img src="../images/your-photo.jpg" alt="" loading="lazy" width="1200" height="400">
</div>
```

### Change the copyright year

Find `2026` in the footer of every page and update it. In VS Code, use Replace in Files to change all at once.

### Remove the "How It Was Built" page

1. Delete the `how-it-was-built/` folder
2. In every page's footer, remove the line: `<a href="../how-it-was-built/">How This Site Was Built</a>`
3. Remove it from the search index in `js/search.js`

---

## Need Help?

This site was built with [Claude Code](https://claude.ai) by Anthropic. If you need to make changes and aren't sure how, you can:

1. Open Claude Code or any AI coding assistant
2. Give it the file you want to change
3. Describe what you want in plain English (e.g., "Change the phone number to 555-123-4567 on every page")
4. It will make the edits for you

That's how this site was built in the first place — and it's how you can maintain it going forward.
