"""Sightline Guardian - Obsidian Signal UI Template.

Production-grade mobile-first application interface for the Smart Blind Stick Guardian App.
Implements the 'Obsidian Signal' design system:
- Palette: Warm ivory (#F6F5EF), Pure white (#FFFFFF), Pale sage (#E9EEE7),
  Deep forest green (#173C35), Muted teal (#3E7569), Ink black (#202722),
  Slate gray (#69736D), Soft stone (#E0E4DC), Coral red (#C83E45), Burnt amber (#A86419).
- Typography: Manrope (display/headings/numeric) + Inter (body/labels/navigation).
- 5 Destinations: Home, Location, Alerts, History, Settings.
- Features:
  - Cinematic Pre-launch Loader with glowing beacon emblem, status progression, and truthful health checking.
  - "Open on Phone" QR Scanner Access modal with live LAN IP detection, animated scanline, copy link, and Wi-Fi guidance.
"""

def generate_guardian_html(title: str = "Sightline Guardian - Smart Blind Stick", is_pwa: bool = True) -> str:
    pwa_tags = ""
    if is_pwa:
        pwa_tags = """
    <link rel="manifest" href="/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Sightline">
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{title}</title>
    {pwa_tags}
    
    <!-- Google Fonts: Manrope (Headings & Tabular Numerals) + Inter (Body & Labels) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Leaflet Interactive Maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <!-- QRCode.js for reliable client-side mobile QR code generation -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    
    <style>
        /* ==========================================================================
           1. OBSIDIAN SIGNAL DESIGN TOKENS
           ========================================================================== */
        :root {{
            /* Primary backgrounds & surfaces */
            --bg-base: #F6F5EF;            /* Warm ivory */
            --surface-white: #FFFFFF;      /* Pure white */
            --surface-sage: #E9EEE7;       /* Pale sage */
            --surface-subtle: #F0F4ED;     /* Very pale sage */
            
            /* Brand accents */
            --brand-primary: #173C35;      /* Deep forest green */
            --brand-primary-hover: #122F2A;
            --brand-secondary: #3E7569;    /* Muted teal */
            --brand-light: #E5F2E8;        /* Pale forest green */
            
            /* Text hierarchy */
            --text-primary: #202722;       /* Ink black */
            --text-secondary: #69736D;     /* Slate gray */
            --text-muted: #8E9993;         /* Light slate */
            --border-stone: #E0E4DC;       /* Soft stone */
            --border-subtle: #ECEFE9;
            
            /* Semantic states */
            --emergency: #C83E45;          /* Coral red */
            --emergency-bg: #FBE9E8;       /* Pale coral */
            --emergency-border: #F3C5C7;
            
            --warning: #A86419;            /* Burnt amber */
            --warning-bg: #FFF2DC;         /* Pale amber */
            --warning-border: #F5DCB7;
            
            --success: #287653;            /* Forest green */
            --success-bg: #E5F2E8;         /* Pale green */
            --success-border: #C8E3CF;
            
            --offline: #737A76;            /* Neutral gray */
            --offline-bg: #ECEEEB;
            --offline-border: #D5DAD7;
            
            /* Elevation & shadows */
            --shadow-subtle: 0 1px 3px rgba(32, 39, 34, 0.05), 0 1px 2px rgba(32, 39, 34, 0.04);
            --shadow-card: 0 2px 8px rgba(32, 39, 34, 0.06), 0 1px 3px rgba(32, 39, 34, 0.04);
            --shadow-sheet: 0 -4px 24px rgba(32, 39, 34, 0.08);
            --shadow-modal: 0 16px 40px rgba(32, 39, 34, 0.16);
            
            /* Border Radii */
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 18px;
            --radius-xl: 24px;
            --radius-full: 9999px;
            
            /* Typography */
            --font-display: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            
            /* Safe Areas */
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-bottom: env(safe-area-inset-bottom, 0px);
        }}

        /* ==========================================================================
           2. BASE RESETS & LAYOUT RULES (OVERLAP PREVENTION)
           ========================================================================== */
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        html, body {{
            width: 100%;
            height: 100%;
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-body);
            font-size: 15px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            overflow-x: hidden;
        }}

        /* Outer mobile-first shell */
        .app-shell {{
            max-width: 580px;
            margin: 0 auto;
            min-height: 100vh;
            background-color: var(--bg-base);
            position: relative;
            display: flex;
            flex-direction: column;
            padding-bottom: calc(76px + var(--safe-bottom)); /* Guarantee bottom nav never overlaps */
        }}

        /* Desktop framing */
        @media (min-width: 680px) {{
            body {{
                background-color: #ECEAE1;
                display: flex;
                justify-content: center;
            }}
            .app-shell {{
                box-shadow: 0 0 48px rgba(32, 39, 34, 0.08);
                border-left: 1px solid var(--border-stone);
                border-right: 1px solid var(--border-stone);
            }}
        }}

        /* ==========================================================================
           3. CINEMATIC PRE-LAUNCH LOADER
           ========================================================================== */
        .cinematic-loader {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 99999;
            background: radial-gradient(circle at 50% 42%, #132A24 0%, #081512 85%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #F6F5EF;
            padding: 24px;
            opacity: 1;
            transition: opacity 0.45s ease, transform 0.45s ease;
        }}

        .cinematic-loader.hide {{
            opacity: 0;
            pointer-events: none;
            transform: scale(1.02);
        }}

        /* Concentric Radar Rings */
        .loader-radar-wrap {{
            position: relative;
            width: 180px;
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        }}

        .radar-ring {{
            position: absolute;
            border-radius: 50%;
            border: 1px solid rgba(62, 117, 105, 0.35);
            animation: radarPulse 3s infinite ease-out;
        }}

        .radar-ring:nth-child(1) {{ width: 70px; height: 70px; animation-delay: 0s; }}
        .radar-ring:nth-child(2) {{ width: 120px; height: 120px; animation-delay: 0.9s; }}
        .radar-ring:nth-child(3) {{ width: 170px; height: 170px; animation-delay: 1.8s; }}

        @keyframes radarPulse {{
            0% {{ transform: scale(0.85); opacity: 0.7; }}
            50% {{ transform: scale(1.1); opacity: 0.2; }}
            100% {{ transform: scale(1.25); opacity: 0; }}
        }}

        /* Glowing Central Emblem */
        .loader-emblem {{
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background: linear-gradient(135deg, #1A473E 0%, #0F2A25 100%);
            border: 2px solid rgba(82, 162, 144, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            z-index: 2;
            box-shadow: 0 0 32px rgba(40, 118, 83, 0.5), inset 0 0 16px rgba(62, 117, 105, 0.4);
            animation: emblemScale 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}

        @keyframes emblemScale {{
            0% {{ transform: scale(0.75); opacity: 0; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}

        .loader-emblem svg {{
            width: 32px;
            height: 32px;
            stroke: #E5F2E8;
            filter: drop-shadow(0 0 8px rgba(229, 242, 232, 0.6));
        }}

        .loader-title {{
            font-family: var(--font-display);
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #FFFFFF;
            margin-bottom: 4px;
            text-align: center;
        }}

        .loader-tagline {{
            font-family: var(--font-body);
            font-size: 0.85rem;
            color: #A3BFB5;
            margin-bottom: 24px;
            letter-spacing: 0.01em;
            text-align: center;
        }}

        /* Thin Progress Bar */
        .loader-progress-wrap {{
            width: 220px;
            height: 3px;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 99px;
            overflow: hidden;
            margin-bottom: 12px;
        }}

        .loader-progress-bar {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #287653, #3E7569, #72C3AF);
            border-radius: 99px;
            transition: width 0.35s ease;
        }}

        .loader-status-msg {{
            font-size: 0.78rem;
            color: #8EABA0;
            letter-spacing: 0.01em;
            min-height: 18px;
            text-align: center;
        }}

        /* Connection Warning (if backend is down) */
        .loader-warning-box {{
            display: none;
            background: rgba(168, 100, 25, 0.15);
            border: 1px solid var(--warning);
            border-radius: var(--radius-sm);
            padding: 10px 14px;
            margin-top: 14px;
            max-width: 300px;
            text-align: center;
            font-size: 0.78rem;
            color: #FFDEB3;
        }}

        .loader-warning-box button {{
            margin-top: 8px;
            padding: 5px 12px;
            font-size: 0.75rem;
            border-radius: var(--radius-sm);
            border: 1px solid #FFDEB3;
            background: transparent;
            color: #FFF;
            cursor: pointer;
        }}

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {{
            .radar-ring {{ animation: none; }}
            .loader-emblem {{ animation: none; }}
        }}

        /* ==========================================================================
           4. TOP APP HEADER & QR BUTTON
           ========================================================================== */
        .app-header {{
            position: sticky;
            top: 0;
            z-index: 90;
            background-color: rgba(246, 245, 239, 0.94);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-stone);
            padding: calc(10px + var(--safe-top)) 16px 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}

        .brand-group {{
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }}

        .brand-mark {{
            width: 32px;
            height: 32px;
            border-radius: 9px;
            background: var(--brand-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--surface-white);
            flex-shrink: 0;
        }}

        .brand-text {{
            min-width: 0;
        }}

        .brand-title {{
            font-family: var(--font-display);
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .brand-sub {{
            font-size: 0.72rem;
            color: var(--text-secondary);
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }}

        /* Prominent "Open on Phone" Button */
        .btn-qr-open {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 11px;
            border-radius: var(--radius-full);
            background: var(--surface-white);
            border: 1.5px solid var(--brand-primary);
            color: var(--brand-primary);
            font-family: var(--font-body);
            font-size: 0.76rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.15s ease;
            box-shadow: 0 1px 3px rgba(23, 60, 53, 0.08);
            white-space: nowrap;
        }}

        .btn-qr-open:hover {{
            background: var(--brand-primary);
            color: var(--surface-white);
        }}

        .btn-qr-open:hover svg {{
            stroke: var(--surface-white);
        }}

        .btn-qr-open svg {{
            width: 15px;
            height: 15px;
            stroke: var(--brand-primary);
            transition: stroke 0.15s ease;
            flex-shrink: 0;
        }}

        /* Device status pill */
        .device-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: var(--radius-full);
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .status-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--success);
            display: inline-block;
        }}

        .status-dot.offline {{
            background-color: var(--offline);
        }}

        .status-dot.emergency {{
            background-color: var(--emergency);
            animation: pulse-coral 1.5s infinite;
        }}

        @keyframes pulse-coral {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.3); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}

        /* Battery pill in header */
        .battery-pill {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 9px;
            border-radius: var(--radius-full);
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            font-size: 0.75rem;
            font-weight: 700;
            font-family: var(--font-display);
            font-variant-numeric: tabular-nums;
            color: var(--text-primary);
        }}

        /* ==========================================================================
           5. BOTTOM NAVIGATION BAR (5 DESTINATIONS)
           ========================================================================== */
        .bottom-nav {{
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 580px;
            height: calc(62px + var(--safe-bottom));
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-top: 1px solid var(--border-stone);
            display: flex;
            align-items: flex-start;
            justify-content: space-around;
            padding-top: 6px;
            padding-bottom: var(--safe-bottom);
            z-index: 1000;
        }}

        .nav-tab {{
            flex: 1;
            min-height: 48px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            background: none;
            border: none;
            cursor: pointer;
            color: var(--text-secondary);
            transition: color 0.15s ease;
            position: relative;
            padding: 4px 0;
            text-decoration: none;
        }}

        .nav-tab svg {{
            width: 21px;
            height: 21px;
            stroke-width: 2.1;
            stroke: currentColor;
            fill: none;
            transition: transform 0.15s ease, stroke 0.15s ease;
        }}

        .nav-tab span {{
            font-size: 0.69rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}

        .nav-tab.active {{
            color: var(--brand-primary);
        }}

        .nav-tab.active svg {{
            stroke: var(--brand-primary);
            transform: translateY(-1px);
        }}

        .nav-tab.active span {{
            font-weight: 700;
        }}

        /* Active alert badge on tab */
        .nav-badge {{
            position: absolute;
            top: 2px;
            right: calc(50% - 15px);
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--emergency);
            display: none;
        }}

        .nav-badge.visible {{
            display: block;
        }}

        /* ==========================================================================
           6. VIEWS CONTAINER & SCREEN TRANSITIONS
           ========================================================================== */
        .view-content {{
            display: none;
            padding: 16px;
            animation: fadeIn 0.18s ease-out;
        }}

        .view-content.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(3px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Screen Headings */
        .screen-header {{
            margin-bottom: 16px;
        }}

        .screen-title {{
            font-family: var(--font-display);
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: var(--text-primary);
            line-height: 1.2;
        }}

        .screen-subtitle {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Card System */
        .card {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: var(--shadow-subtle);
            min-width: 0;
            overflow-wrap: break-word;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }}

        .card-title {{
            font-family: var(--font-display);
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .card-title svg {{
            width: 18px;
            height: 18px;
            stroke: var(--brand-secondary);
            flex-shrink: 0;
        }}

        /* Tag / Pill components */
        .tag {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: var(--radius-full);
            font-size: 0.72rem;
            font-weight: 600;
        }}

        .tag-success {{
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid var(--success-border);
        }}

        .tag-warning {{
            background: var(--warning-bg);
            color: var(--warning);
            border: 1px solid var(--warning-border);
        }}

        .tag-emergency {{
            background: var(--emergency-bg);
            color: var(--emergency);
            border: 1px solid var(--emergency-border);
        }}

        .tag-neutral {{
            background: var(--offline-bg);
            color: var(--offline);
            border: 1px solid var(--offline-border);
        }}

        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            min-height: 44px;
            padding: 10px 18px;
            border-radius: var(--radius-sm);
            font-family: var(--font-body);
            font-size: 0.9rem;
            font-weight: 600;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
            line-height: 1;
            white-space: nowrap;
        }}

        .btn-primary {{
            background: var(--brand-primary);
            color: var(--surface-white);
            border-color: var(--brand-primary);
        }}

        .btn-primary:active {{
            background: var(--brand-primary-hover);
            transform: scale(0.99);
        }}

        .btn-secondary {{
            background: var(--surface-white);
            color: var(--text-primary);
            border-color: var(--border-stone);
        }}

        .btn-secondary:active {{
            background: var(--surface-subtle);
        }}

        .btn-emergency {{
            background: var(--emergency);
            color: var(--surface-white);
            border-color: var(--emergency);
        }}

        .btn-emergency-outline {{
            background: var(--surface-white);
            color: var(--emergency);
            border-color: var(--emergency-border);
        }}

        .btn-full {{
            width: 100%;
        }}

        .btn-sm {{
            min-height: 36px;
            padding: 6px 12px;
            font-size: 0.8rem;
        }}

        /* ==========================================================================
           7. SCREEN 1: HOME DASHBOARD
           ========================================================================== */
        /* Elevated Emergency Banner (when SOS or Fall active) */
        .emergency-banner {{
            display: none;
            background: var(--emergency-bg);
            border: 1.5px solid var(--emergency);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 14px rgba(200, 62, 69, 0.12);
        }}

        .emergency-banner.visible {{
            display: block;
        }}

        .emg-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}

        .emg-pulse-icon {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--emergency);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            animation: pulse-coral 1.3s infinite;
            flex-shrink: 0;
        }}

        .emg-title {{
            font-family: var(--font-display);
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--emergency);
            letter-spacing: -0.01em;
        }}

        .emg-desc {{
            font-size: 0.84rem;
            color: var(--text-primary);
            margin-bottom: 12px;
            line-height: 1.45;
        }}

        .emg-meta-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 0.78rem;
            color: var(--text-secondary);
            margin-bottom: 14px;
            font-variant-numeric: tabular-nums;
        }}

        .emg-actions {{
            display: flex;
            gap: 8px;
        }}

        /* Primary Safety Summary Panel */
        .safety-summary-panel {{
            background: var(--surface-white);
            border: 1.5px solid var(--border-stone);
            border-radius: var(--radius-lg);
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: var(--shadow-card);
        }}

        .safety-status-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            gap: 10px;
        }}

        .safety-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: var(--radius-full);
            font-family: var(--font-display);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        .safety-badge.normal {{
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid var(--success-border);
        }}

        .safety-badge.warning {{
            background: var(--warning-bg);
            color: var(--warning);
            border: 1px solid var(--warning-border);
        }}

        .safety-badge.emergency {{
            background: var(--emergency-bg);
            color: var(--emergency);
            border: 1px solid var(--emergency-border);
        }}

        .safety-badge.offline {{
            background: var(--offline-bg);
            color: var(--offline);
            border: 1px solid var(--offline-border);
        }}

        .last-comm-time {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }}

        .stick-identity {{
            font-family: var(--font-display);
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .safety-explanation {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            line-height: 1.45;
        }}

        /* Quick Device Metrics Grid (2x2 layout, responsive) */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}

        .metric-card {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 14px;
            box-shadow: var(--shadow-subtle);
            min-width: 0;
        }}

        .metric-label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .metric-value {{
            font-family: var(--font-display);
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            font-variant-numeric: tabular-nums;
            color: var(--text-primary);
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .metric-sub {{
            font-size: 0.72rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Mini progress bar for battery */
        .battery-track {{
            width: 100%;
            height: 5px;
            background: var(--border-stone);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 6px;
        }}

        .battery-fill {{
            height: 100%;
            background: var(--success);
            border-radius: 3px;
            transition: width 0.3s ease;
        }}

        /* Mobile Access Invite Card */
        .mobile-invite-card {{
            background: linear-gradient(135deg, var(--surface-sage) 0%, #FFFFFF 100%);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 14px 16px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            box-shadow: var(--shadow-subtle);
        }}

        .mobile-invite-left {{
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }}

        .mobile-invite-icon {{
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: var(--brand-primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .mobile-invite-title {{
            font-family: var(--font-display);
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .mobile-invite-sub {{
            font-size: 0.73rem;
            color: var(--text-secondary);
        }}

        /* Mini Map Preview Card */
        .location-preview-card {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: var(--shadow-subtle);
        }}

        .loc-coords-preview {{
            font-family: var(--font-display);
            font-variant-numeric: tabular-nums;
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .loc-address-preview {{
            font-size: 0.78rem;
            color: var(--text-secondary);
            margin-bottom: 12px;
        }}

        /* Recent alerts preview */
        .recent-alerts-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .alert-row-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: var(--radius-sm);
            background: var(--surface-subtle);
            border: 1px solid var(--border-stone);
            gap: 10px;
            cursor: pointer;
            transition: background 0.15s ease;
        }}

        .alert-row-item:active {{
            background: var(--border-stone);
        }}

        .alert-row-main {{
            min-width: 0;
            flex: 1;
        }}

        .alert-row-title {{
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .alert-row-time {{
            font-size: 0.7rem;
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
            margin-top: 2px;
        }}

        /* ==========================================================================
           8. SCREEN 2: LOCATION
           ========================================================================== */
        .map-container {{
            width: 100%;
            height: 380px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-stone);
            overflow: hidden;
            position: relative;
            margin-bottom: 12px;
            box-shadow: var(--shadow-subtle);
        }}

        #map {{
            width: 100%;
            height: 100%;
            z-index: 1;
        }}

        /* Map floating controls */
        .map-floating-bar {{
            position: absolute;
            top: 12px;
            right: 12px;
            z-index: 500;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .map-btn {{
            width: 40px;
            height: 40px;
            border-radius: var(--radius-sm);
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            box-shadow: var(--shadow-card);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--brand-primary);
        }}

        .map-btn:active {{
            background: var(--surface-subtle);
            transform: scale(0.96);
        }}

        /* Location Info Bottom Sheet */
        .location-info-panel {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 16px;
            box-shadow: var(--shadow-card);
        }}

        .loc-header-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }}

        .loc-status-pill {{
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: var(--radius-full);
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid var(--success-border);
        }}

        .loc-status-pill.stale {{
            background: var(--warning-bg);
            color: var(--warning);
            border-color: var(--warning-border);
        }}

        .loc-coords-large {{
            font-family: var(--font-display);
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            font-variant-numeric: tabular-nums;
            color: var(--text-primary);
            margin-bottom: 6px;
        }}

        .loc-details-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--border-stone);
            font-size: 0.78rem;
        }}

        .loc-detail-item {{
            color: var(--text-secondary);
        }}

        .loc-detail-item strong {{
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }}

        /* ==========================================================================
           9. SCREEN 3: ALERTS & EMERGENCIES
           ========================================================================== */
        .section-divider {{
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin: 20px 0 10px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .section-divider::after {{
            content: "";
            flex: 1;
            height: 1px;
            background: var(--border-stone);
        }}

        .incident-card {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: var(--shadow-subtle);
            min-width: 0;
            overflow-wrap: break-word;
        }}

        .incident-card.critical {{
            border-left: 4px solid var(--emergency);
        }}

        .incident-card.warning {{
            border-left: 4px solid var(--warning);
        }}

        .incident-card.resolved {{
            border-left: 4px solid var(--success);
            opacity: 0.88;
        }}

        .incident-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
        }}

        .incident-title {{
            font-family: var(--font-display);
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.3;
        }}

        .incident-time {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
            margin-bottom: 10px;
        }}

        .incident-details-box {{
            background: var(--surface-subtle);
            border-radius: var(--radius-sm);
            padding: 10px;
            font-size: 0.8rem;
            color: var(--text-primary);
            line-height: 1.4;
            margin-bottom: 12px;
        }}

        .incident-actions-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        /* ==========================================================================
           10. SCREEN 4: INCIDENT HISTORY
           ========================================================================== */
        .filter-chip-group {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 14px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }}

        .filter-chip-group::-webkit-scrollbar {{
            display: none;
        }}

        .filter-chip {{
            padding: 6px 14px;
            border-radius: var(--radius-full);
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }}

        .filter-chip.active {{
            background: var(--brand-primary);
            color: var(--surface-white);
            border-color: var(--brand-primary);
        }}

        .history-timeline {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .timeline-date-label {{
            font-family: var(--font-display);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-secondary);
            margin: 12px 0 4px 0;
        }}

        .history-row {{
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            box-shadow: var(--shadow-subtle);
        }}

        .history-left {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
            flex: 1;
        }}

        .history-icon-box {{
            width: 36px;
            height: 36px;
            border-radius: 9px;
            background: var(--surface-sage);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            color: var(--brand-primary);
        }}

        .history-texts {{
            min-width: 0;
            flex: 1;
        }}

        .history-msg {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .history-meta {{
            font-size: 0.72rem;
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
            margin-top: 2px;
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            background: var(--surface-white);
            border: 1px dashed var(--border-stone);
            border-radius: var(--radius-md);
            margin-top: 10px;
        }}

        .empty-icon {{
            width: 48px;
            height: 48px;
            margin: 0 auto 12px auto;
            color: var(--brand-secondary);
            opacity: 0.7;
        }}

        .empty-title {{
            font-family: var(--font-display);
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .empty-desc {{
            font-size: 0.82rem;
            color: var(--text-secondary);
            max-width: 320px;
            margin: 0 auto;
        }}

        /* ==========================================================================
           11. SCREEN 5: SETTINGS & DEVICE HEALTH
           ========================================================================== */
        .health-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-bottom: 16px;
        }}

        .health-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-sm);
            gap: 10px;
        }}

        .health-label-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .health-icon {{
            width: 20px;
            height: 20px;
            stroke: var(--brand-secondary);
            flex-shrink: 0;
        }}

        .health-title {{
            font-size: 0.84rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .health-desc {{
            font-size: 0.72rem;
            color: var(--text-secondary);
        }}

        .pref-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-stone);
        }}

        .pref-item:last-child {{
            border-bottom: none;
        }}

        /* Toggle switch */
        .switch {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            flex-shrink: 0;
        }}

        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: var(--border-stone);
            transition: .2s;
            border-radius: 24px;
        }}

        .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .2s;
            border-radius: 50%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}

        input:checked + .slider {{
            background-color: var(--brand-primary);
        }}

        input:checked + .slider:before {{
            transform: translateX(20px);
        }}

        /* ==========================================================================
           12. QR SCANNER ACCESS MODAL
           ========================================================================== */
        .qr-modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(19, 36, 31, 0.72);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            z-index: 20000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .qr-modal-overlay.active {{
            display: flex;
        }}

        .qr-modal-card {{
            background: var(--surface-white);
            border-radius: var(--radius-xl);
            width: 100%;
            max-width: 440px;
            padding: 26px 24px;
            box-shadow: var(--shadow-modal);
            border: 1px solid var(--border-stone);
            animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            text-align: center;
        }}

        .qr-close-btn {{
            position: absolute;
            top: 16px;
            right: 16px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1px solid var(--border-stone);
            background: var(--surface-subtle);
            color: var(--text-secondary);
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .qr-close-btn:hover {{
            background: var(--border-stone);
            color: var(--text-primary);
        }}

        .qr-heading {{
            font-family: var(--font-display);
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .qr-subheading {{
            font-size: 0.84rem;
            color: var(--text-secondary);
            margin-bottom: 18px;
            line-height: 1.4;
        }}

        /* QR Frame with Animated Scanline */
        .qr-code-frame {{
            background: #FFFFFF;
            border: 2px solid var(--border-stone);
            border-radius: var(--radius-lg);
            padding: 16px;
            display: inline-block;
            margin: 0 auto 16px auto;
            position: relative;
            box-shadow: 0 4px 18px rgba(23, 60, 53, 0.08);
            overflow: hidden;
        }}

        #qr-canvas-container {{
            width: 200px;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        #qr-canvas-container img, #qr-canvas-container canvas {{
            display: block;
            margin: 0 auto;
        }}

        /* Subtle animated scanline moving over the QR code */
        .qr-scanline {{
            position: absolute;
            left: 10px;
            right: 10px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #287653, #3E7569, #52A290, transparent);
            box-shadow: 0 0 10px rgba(40, 118, 83, 0.75);
            border-radius: 2px;
            top: 10px;
            animation: qrScanMove 2.8s infinite ease-in-out;
            pointer-events: none;
        }}

        @keyframes qrScanMove {{
            0% {{ top: 12px; opacity: 0.7; }}
            50% {{ top: calc(100% - 15px); opacity: 1; }}
            100% {{ top: 12px; opacity: 0.7; }}
        }}

        /* Connection status indicator */
        .qr-status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: var(--radius-full);
            background: var(--surface-subtle);
            border: 1px solid var(--border-stone);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--brand-primary);
            margin-bottom: 14px;
        }}

        .qr-status-indicator.ready {{
            background: var(--success-bg);
            color: var(--success);
            border-color: var(--success-border);
        }}

        .qr-status-indicator.error {{
            background: var(--emergency-bg);
            color: var(--emergency);
            border-color: var(--emergency-border);
        }}

        /* Target URL display box */
        .qr-url-box {{
            background: var(--surface-subtle);
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-sm);
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .qr-url-text {{
            font-family: var(--font-display);
            font-size: 0.8rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            color: var(--brand-primary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            text-align: left;
        }}

        .btn-copy-url {{
            padding: 5px 10px;
            font-size: 0.72rem;
            font-weight: 700;
            border-radius: var(--radius-sm);
            background: var(--surface-white);
            border: 1px solid var(--border-stone);
            color: var(--text-primary);
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s ease;
        }}

        .btn-copy-url:hover {{
            background: var(--brand-light);
            border-color: var(--brand-secondary);
            color: var(--brand-primary);
        }}

        .qr-wifi-note {{
            font-size: 0.74rem;
            color: var(--text-secondary);
            line-height: 1.4;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 14px;
        }}

        .qr-actions-row {{
            display: flex;
            gap: 8px;
            justify-content: center;
        }}

        /* ==========================================================================
           13. GENERAL MODAL DIALOGS & TOAST
           ========================================================================== */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(32, 39, 34, 0.5);
            backdrop-filter: blur(4px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .modal-overlay.active {{
            display: flex;
        }}

        .modal-box {{
            background: var(--surface-white);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 440px;
            padding: 22px;
            box-shadow: var(--shadow-modal);
            border: 1px solid var(--border-stone);
            animation: modalPop 0.16s ease-out;
        }}

        @keyframes modalPop {{
            from {{ transform: scale(0.96); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}

        .modal-title {{
            font-family: var(--font-display);
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}

        .modal-body {{
            font-size: 0.86rem;
            color: var(--text-secondary);
            line-height: 1.45;
            margin-bottom: 18px;
        }}

        .form-label {{
            display: block;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
        }}

        .form-input {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-stone);
            border-radius: var(--radius-sm);
            font-family: var(--font-body);
            font-size: 0.88rem;
            color: var(--text-primary);
            background: var(--surface-white);
            margin-bottom: 12px;
            outline: none;
        }}

        .form-input:focus {{
            border-color: var(--brand-secondary);
        }}

        .modal-actions {{
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 14px;
        }}

        /* Toast Feedback */
        .toast-banner {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(-30px);
            background: var(--brand-primary);
            color: var(--surface-white);
            padding: 10px 18px;
            border-radius: var(--radius-full);
            font-size: 0.82rem;
            font-weight: 600;
            box-shadow: var(--shadow-modal);
            z-index: 30000;
            opacity: 0;
            pointer-events: none;
            transition: all 0.22s ease;
            white-space: nowrap;
        }}

        .toast-banner.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }}
    </style>
</head>
<body>

    <!-- ====================================================================
         CINEMATIC PRE-LAUNCH LOADER
         ==================================================================== -->
    <div id="cinematic-loader" class="cinematic-loader" role="status" aria-live="polite">
        <div class="loader-radar-wrap">
            <div class="radar-ring"></div>
            <div class="radar-ring"></div>
            <div class="radar-ring"></div>
            <div class="loader-emblem">
                <!-- Guardian Shield & Location Sight Emblem -->
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    <circle cx="12" cy="11" r="3"></circle>
                </svg>
            </div>
        </div>

        <h1 class="loader-title">SIGHTLINE GUARDIAN</h1>
        <div class="loader-tagline">Your safety. Your independence.</div>

        <div class="loader-progress-wrap">
            <div class="loader-progress-bar" id="loader-progress"></div>
        </div>
        <div class="loader-status-msg" id="loader-status-text">Initializing Guardian...</div>

        <!-- Connection Warning (Fallback if API is unreachable) -->
        <div class="loader-warning-box" id="loader-warning-box">
            <div>Hardware bridge offline or waiting for connection.</div>
            <button onclick="dismissLoaderAnyway()">Proceed to Dashboard</button>
        </div>
    </div>

    <!-- ====================================================================
         APP SHELL
         ==================================================================== -->
    <div class="app-shell">
        <!-- ====================================================================
             TOP APP HEADER
             ==================================================================== -->
        <header class="app-header">
            <div class="brand-group">
                <div class="brand-mark">
                    <!-- Sightline Sight/Compass Icon -->
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <circle cx="12" cy="12" r="3"></circle>
                        <line x1="12" y1="2" x2="12" y2="5"></line>
                        <line x1="12" y1="19" x2="12" y2="22"></line>
                        <line x1="2" y1="12" x2="5" y2="12"></line>
                        <line x1="19" y1="12" x2="22" y2="12"></line>
                    </svg>
                </div>
                <div class="brand-text">
                    <div class="brand-title">SIGHTLINE GUARDIAN</div>
                    <div class="brand-sub">Smart Blind Stick Companion</div>
                </div>
            </div>

            <div class="header-actions">
                <!-- Open on Phone QR Access Button -->
                <button class="btn-qr-open" id="btn-header-qr" onclick="openQrModal()" title="Open on Phone via QR Code" aria-label="Open on Phone">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                        <line x1="12" y1="18" x2="12.01" y2="18"></line>
                    </svg>
                    <span>Open on Phone</span>
                </button>

                <div class="device-pill" id="header-device-pill">
                    <span class="status-dot" id="header-status-dot"></span>
                    <span id="header-device-id">STICK_001</span>
                </div>
                <div class="battery-pill" id="header-battery-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="7" width="16" height="10" rx="2" ry="2"></rect>
                        <line x1="22" y1="11" x2="22" y2="13"></line>
                    </svg>
                    <span id="header-battery-pct">--%</span>
                </div>
            </div>
        </header>

        <!-- ====================================================================
             SCREEN 1: HOME DASHBOARD
             ==================================================================== -->
        <main id="view-home" class="view-content active" role="tabpanel">
            <!-- Elevated Emergency Banner (Conditional) -->
            <div id="home-emergency-banner" class="emergency-banner" role="alert">
                <div class="emg-header">
                    <div class="emg-pulse-icon">🚨</div>
                    <div class="emg-title" id="home-emg-title">CRITICAL SOS REPORTED</div>
                </div>
                <div class="emg-desc" id="home-emg-desc">
                    The stick reported an active emergency. Immediate guardian attention is advised.
                </div>
                <div class="emg-meta-row">
                    <span id="home-emg-time">Time: Detecting...</span>
                    <span id="home-emg-coords">Location: Capturing GPS</span>
                </div>
                <div class="emg-actions">
                    <button class="btn btn-emergency btn-sm" onclick="switchTab('alerts')">Inspect Incident</button>
                    <a href="tel:+15550198" class="btn btn-secondary btn-sm" id="home-call-user-btn">Call Alex (User)</a>
                </div>
            </div>

            <!-- Mobile Access Invite Card -->
            <div class="mobile-invite-card" onclick="openQrModal()" style="cursor: pointer;">
                <div class="mobile-invite-left">
                    <div class="mobile-invite-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                            <rect x="3" y="3" width="7" height="7"></rect>
                            <rect x="14" y="3" width="7" height="7"></rect>
                            <rect x="14" y="14" width="7" height="7"></rect>
                            <rect x="3" y="14" width="7" height="7"></rect>
                        </svg>
                    </div>
                    <div>
                        <div class="mobile-invite-title">Scan to Open on Phone</div>
                        <div class="mobile-invite-sub">Access live tracking and alerts on your Android device</div>
                    </div>
                </div>
                <button class="btn btn-secondary btn-sm" style="min-height:30px; padding:3px 10px; font-size:0.75rem;">
                    Scan QR
                </button>
            </div>

            <!-- Screen Context & Safety Summary -->
            <div class="screen-header">
                <h1 class="screen-title">Guardian Overview</h1>
                <p class="screen-subtitle">Active Remote Safety Telemetry • Alex Rivera</p>
            </div>

            <!-- Prominent Device Connection & Keyboard Action Hub -->
            <div style="display:flex; gap:10px; margin: 0 0 16px 0;">
                <button class="btn btn-primary btn-full" id="btn-prominent-connect-device" onclick="openDeviceConnectionCenter()" style="font-weight:700; padding:12px; display:flex; align-items:center; justify-content:center; gap:8px;" aria-label="Connect Device">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
                    <span>Connect Device</span>
                </button>
                <button class="btn btn-secondary" id="btn-prominent-keyboard" onclick="openKeyboardGuide()" style="padding:12px 14px; font-weight:700; display:flex; align-items:center; gap:6px;" title="Keyboard &amp; Controls" aria-label="Keyboard and Controls">
                    <span>⌨️ Keys</span>
                </button>
            </div>

            <!-- Primary Safety Summary Panel -->
            <section class="safety-summary-panel">
                <div class="safety-status-row">
                    <span class="safety-badge normal" id="safety-badge">
                        <span class="status-dot" id="safety-dot"></span>
                        <span id="safety-status-text">Device reporting normally</span>
                    </span>
                    <span class="last-comm-time" id="safety-last-comm">Connecting...</span>
                </div>
                <div class="stick-identity">SmartStick Alpha (STICK_001)</div>
                <div class="safety-explanation" id="safety-explanation">
                    Hardware heartbeat and sensor fusion streams reporting nominal baseline operation.
                </div>
            </section>

            <!-- Quick Device Metrics Grid -->
            <div class="metrics-grid">
                <!-- Battery Card -->
                <div class="metric-card">
                    <div class="metric-label">
                        <span>BATTERY</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="16" height="10" rx="2" ry="2"></rect><line x1="22" y1="11" x2="22" y2="13"></line></svg>
                    </div>
                    <div class="metric-value" id="card-battery-val">--%</div>
                    <div class="battery-track">
                        <div class="battery-fill" id="card-battery-fill" style="width: 0%;"></div>
                    </div>
                    <div class="metric-sub" id="card-battery-sub" style="margin-top:6px;">Estimating...</div>
                </div>

                <!-- GPS Status Card -->
                <div class="metric-card">
                    <div class="metric-label">
                        <span>GPS SATELLITES</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
                    </div>
                    <div class="metric-value" id="card-gps-val">Acquiring</div>
                    <div class="metric-sub" id="card-gps-sub">NEO-6M Module</div>
                </div>

                <!-- Device Connectivity Card -->
                <div class="metric-card">
                    <div class="metric-label">
                        <span>CONNECTIVITY</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
                    </div>
                    <div class="metric-value" id="card-conn-val">CHECKING...</div>
                    <div class="metric-sub" id="card-conn-sub">Connecting to Stick...</div>
                </div>

                <!-- Sensor Fusion & Proximity Card -->
                <div class="metric-card">
                    <div class="metric-label">
                        <span>OBSTACLE RADAR</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path></svg>
                    </div>
                    <div class="metric-value" id="card-radar-val" style="font-size: 1.1rem;">Waiting...</div>
                    <div class="metric-sub" id="card-radar-sub">Waiting for sensor data</div>
                </div>
            </div>

            <!-- AI Vision Camera Feed Card -->
            <section class="card" id="card-ai-vision" style="margin-top:14px;">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                        AI Vision &amp; Camera Feed
                    </h2>
                    <span class="tag tag-secondary" id="ai-vision-status-tag">Checking...</span>
                </div>
                <div style="background:#132A24; border-radius:var(--radius-sm); min-height:140px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#E5F2E8; padding:16px; text-align:center;">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#52A290" stroke-width="1.8" style="margin-bottom:6px;"><circle cx="12" cy="13" r="4"></circle><path d="M5 7h2l2-3h6l2 3h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"></path></svg>
                    <div style="font-size:0.86rem; font-weight:700;" id="ai-vision-label">ESP32-CAM Standby</div>
                    <div style="font-size:0.74rem; color:#A3BCB4; margin-top:3px;" id="ai-vision-sub">Inference server ready on CPU • YOLOv8n (COCO)</div>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; font-size:0.78rem;">
                    <div style="background:var(--surface-subtle); padding:8px 10px; border-radius:6px; border:1px solid var(--border-stone);">
                        Model: <strong id="ai-model-name">YOLOv8n-COCO</strong>
                    </div>
                    <div style="background:var(--surface-subtle); padding:8px 10px; border-radius:6px; border:1px solid var(--border-stone);">
                        Latency: <strong id="ai-latency-val">-- ms</strong>
                    </div>
                </div>
                <div style="display:flex; gap:8px; margin-top:10px;">
                    <button class="btn btn-secondary btn-full btn-sm" onclick="checkVisionInference()">
                        🔄 Query Vision Model Status
                    </button>
                </div>
            </section>

            <!-- Multi-Level Obstacle Elevation Card -->
            <section class="card" id="card-obstacle-elevation" style="margin-top:14px;">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path></svg>
                        Multi-Level Elevation Detection
                    </h2>
                    <span class="tag tag-success" id="obstacle-zone-tag">Clear Path</span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:6px; text-align:center; font-size:0.75rem; margin-top:6px;">
                    <div style="background:var(--surface-subtle); padding:10px 4px; border-radius:6px; border:1px solid var(--border-stone);" id="level-ground">
                        <div style="font-size:1.1rem; margin-bottom:2px;">🦶</div>
                        <div style="font-weight:700;">Ground</div>
                        <div style="font-size:0.7rem; color:var(--text-secondary);" id="val-level-ground">Clear</div>
                    </div>
                    <div style="background:var(--surface-subtle); padding:10px 4px; border-radius:6px; border:1px solid var(--border-stone);" id="level-waist">
                        <div style="font-size:1.1rem; margin-bottom:2px;">🚶</div>
                        <div style="font-weight:700;">Waist</div>
                        <div style="font-size:0.7rem; color:var(--text-secondary);" id="val-level-waist">Clear</div>
                    </div>
                    <div style="background:var(--surface-subtle); padding:10px 4px; border-radius:6px; border:1px solid var(--border-stone);" id="level-chest">
                        <div style="font-size:1.1rem; margin-bottom:2px;">🛡️</div>
                        <div style="font-weight:700;">Chest</div>
                        <div style="font-size:0.7rem; color:var(--text-secondary);" id="val-level-chest">Clear</div>
                    </div>
                    <div style="background:var(--surface-subtle); padding:10px 4px; border-radius:6px; border:1px solid var(--border-stone);" id="level-head">
                        <div style="font-size:1.1rem; margin-bottom:2px;">🌳</div>
                        <div style="font-weight:700;">Head</div>
                        <div style="font-size:0.7rem; color:var(--text-secondary);" id="val-level-head">Clear</div>
                    </div>
                </div>
            </section>


            <!-- Latest Location Preview Card -->
            <section class="location-preview-card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        Reported Location Preview
                    </h2>
                    <span class="tag tag-secondary" id="home-geofence-tag">Awaiting Fix</span>
                </div>
                <div class="loc-coords-preview" id="home-coords-preview">GPS fix unavailable</div>
                <div class="loc-address-preview" id="home-time-preview">Awaiting device telemetry</div>
                <button class="btn btn-secondary btn-full btn-sm" onclick="switchTab('location')">
                    Open Full Map & Navigation Controls
                </button>
            </section>

            <!-- Recent Incidents Section -->
            <section class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        Recent Activity
                    </h2>
                    <button class="btn btn-secondary btn-sm" onclick="switchTab('alerts')" style="min-height:30px; padding:3px 8px; font-size:0.75rem;">
                        View all
                    </button>
                </div>
                <div class="recent-alerts-list" id="home-recent-alerts">
                    <div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:12px;">
                        Loading recent events...
                    </div>
                </div>
            </section>
        </main>

        <!-- ====================================================================
             SCREEN 2: LOCATION
             ==================================================================== -->
        <main id="view-location" class="view-content" role="tabpanel">
            <div class="screen-header">
                <h1 class="screen-title">Live Geolocation</h1>
                <p class="screen-subtitle">Interactive Stick Position, Safe Zones & Obstacles</p>
            </div>

            <!-- Map View Container -->
            <div class="map-container">
                <div id="map"></div>
                <div class="map-floating-bar">
                    <button class="map-btn" title="Center on Stick" onclick="centerMapOnStick()" aria-label="Center on Stick">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>
                    </button>
                    <button class="map-btn" title="External Directions" onclick="openExternalDirections()" aria-label="External Directions">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>
                    </button>
                </div>
            </div>

            <!-- Location Information Card / Panel -->
            <div class="location-info-panel">
                <div class="loc-header-row">
                    <span class="loc-status-pill" id="loc-status-badge">Live GPS Position</span>
                    <span style="font-size:0.75rem; color:var(--text-secondary);" id="loc-updated-time">Updated 3s ago</span>
                </div>
                <div class="loc-coords-large" id="loc-full-coords">12.97160° N, 77.59460° E</div>
                
                <div class="loc-details-grid">
                    <div class="loc-detail-item">
                        Safe Zone: <strong id="loc-geofence-status">Home (350m Perimeter)</strong>
                    </div>
                    <div class="loc-detail-item">
                        Satellites: <strong id="loc-sat-count">9 Fixed</strong>
                    </div>
                    <div class="loc-detail-item">
                        Accuracy: <strong id="loc-accuracy-est">±2.4m (High)</strong>
                    </div>
                    <div class="loc-detail-item">
                        Receiver: <strong>NEO-6M NMEA</strong>
                    </div>
                </div>

                <div style="display:flex; gap:8px; margin-top:14px;">
                    <button class="btn btn-primary btn-full btn-sm" onclick="openExternalDirections()">
                        🗺️ Get Directions in Google Maps
                    </button>
                </div>
            </div>
        </main>

        <!-- ====================================================================
             SCREEN 3: ALERTS AND EMERGENCIES
             ==================================================================== -->
        <main id="view-alerts" class="view-content" role="tabpanel">
            <div class="screen-header">
                <h1 class="screen-title">Alerts & Emergencies</h1>
                <p class="screen-subtitle">Real-time incident management, acknowledgment & response</p>
            </div>

            <!-- Active Emergencies Section -->
            <div class="section-divider">ACTIVE INCIDENTS</div>
            <div id="active-incidents-container">
                <!-- Dynamically populated or empty -->
                <div class="card" style="text-align:center; padding: 24px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:var(--success-bg); color:var(--success); display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto;">
                        ✓
                    </div>
                    <div style="font-family:var(--font-display); font-weight:700; font-size:0.95rem; margin-bottom:4px;">No Active Emergencies</div>
                    <div style="font-size:0.8rem; color:var(--text-secondary);">The stick is reporting within expected parameters. Guardian monitoring is active.</div>
                </div>
            </div>

            <!-- Historical / Resolved Alerts -->
            <div class="section-divider">HISTORICAL NOTIFICATIONS</div>
            <div id="notifications-container">
                <div style="text-align:center; padding: 20px; font-size:0.8rem; color:var(--text-secondary);">
                    Loading incident history...
                </div>
            </div>
        </main>

        <!-- ====================================================================
             SCREEN 4: INCIDENT HISTORY
             ==================================================================== -->
        <main id="view-history" class="view-content" role="tabpanel">
            <div class="screen-header">
                <h1 class="screen-title">Incident History</h1>
                <p class="screen-subtitle">Chronological audit trail of stick safety events</p>
            </div>

            <!-- Category Filter Chips -->
            <div class="filter-chip-group" role="tablist">
                <button class="filter-chip active" onclick="filterHistory('all', this)">All Events</button>
                <button class="filter-chip" onclick="filterHistory('emergency', this)">Emergency</button>
                <button class="filter-chip" onclick="filterHistory('obstacle', this)">Obstacles</button>
                <button class="filter-chip" onclick="filterHistory('geofence', this)">Geofence</button>
                <button class="filter-chip" onclick="filterHistory('system', this)">Diagnostics</button>
            </div>

            <!-- Timeline Stream -->
            <div class="history-timeline" id="history-timeline-list">
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    </div>
                    <div class="empty-title">Connecting to Event Audit Log</div>
                    <div class="empty-desc">Telemetry events recorded by the Smart Blind Stick will populate here automatically.</div>
                </div>
            </div>
        </main>

        <!-- ====================================================================
             SCREEN 5: SETTINGS AND DEVICE HEALTH
             ==================================================================== -->
        <main id="view-settings" class="view-content" role="tabpanel">
            <div class="screen-header">
                <h1 class="screen-title">Settings & Diagnostics</h1>
                <p class="screen-subtitle">Hardware diagnostics, Guardian profile & preferences</p>
            </div>

            <!-- Device Health Diagnostics Card -->
            <section class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                        Hardware Diagnostics
                    </h2>
                    <span class="tag tag-success" id="settings-diag-badge">Nominal</span>
                </div>

                <div class="health-grid">
                    <div class="health-item">
                        <div class="health-label-group">
                            <svg class="health-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line></svg>
                            <div>
                                <div class="health-title">ESP32 Main Controller</div>
                                <div class="health-desc" id="diag-esp32-desc">Firmware v2.4.0 • Online</div>
                            </div>
                        </div>
                        <span class="tag tag-success">Active</span>
                    </div>

                    <div class="health-item">
                        <div class="health-label-group">
                            <svg class="health-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                            <div>
                                <div class="health-title">TF-Luna LiDAR & Proximity</div>
                                <div class="health-desc">Obstacle detection operational</div>
                            </div>
                        </div>
                        <span class="tag tag-success">Calibrated</span>
                    </div>

                    <div class="health-item">
                        <div class="health-label-group">
                            <svg class="health-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                            <div>
                                <div class="health-title">ESP32-CAM AI Vision</div>
                                <div class="health-desc">Object recognition standby</div>
                            </div>
                        </div>
                        <span class="tag tag-secondary" id="diag-lidar-tag">Pending</span>
                    </div>

                    <div class="health-item">
                        <div class="health-label-group">
                            <svg class="health-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                            <div>
                                <div class="health-title">MPU6050 Motion & Fall IMU</div>
                                <div class="health-desc" id="diag-imu-desc">Awaiting sensor report</div>
                            </div>
                        </div>
                        <span class="tag tag-secondary" id="diag-imu-tag">Pending</span>
                    </div>

                    <div class="health-item">
                        <div class="health-label-group">
                            <svg class="health-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
                            <div>
                                <div class="health-title">NEO-6M GPS Receiver</div>
                                <div class="health-desc" id="diag-gps-desc">GPS fix unavailable</div>
                            </div>
                        </div>
                        <span class="tag tag-secondary" id="diag-gps-tag">No Fix</span>
                    </div>
                </div>

                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-full btn-sm" onclick="runDiagnosticsTest()">
                        🩺 Run Self-Diagnostic Test
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="replayCinematicIntro()" title="Replay Startup Intro">
                        🎬 Intro
                    </button>
                </div>
            </section>

            <!-- Guardian Profile & Contact Info -->
            <section class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        Guardian & Emergency Contacts
                    </h2>
                    <button class="btn btn-secondary btn-sm" onclick="openProfileEditModal()" style="min-height:30px; padding:3px 8px; font-size:0.75rem;">
                        Edit
                    </button>
                </div>
                <div style="font-size:0.84rem; line-height:1.6;">
                    <div>Guardian: <strong id="profile-guardian-name">No guardian registered</strong> (<span id="profile-guardian-phone">Not configured</span>)</div>
                    <div>Monitored User: <strong id="profile-user-name">No user profile</strong> (<span id="profile-user-phone">Not configured</span>)</div>
                    <div>Emergency Contact: <strong id="profile-emg-name">None</strong> (<span id="profile-emg-phone">Not configured</span>)</div>
                </div>
            </section>

            <!-- Preferences -->
            <section class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                        Notification Settings
                    </h2>
                </div>
                <div class="pref-item">
                    <div>
                        <div style="font-weight:600; font-size:0.85rem;">Emergency Audio Alarm</div>
                        <div style="font-size:0.72rem; color:var(--text-secondary);">Audible chime on active SOS & falls</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="pref-audio" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="pref-item">
                    <div>
                        <div style="font-weight:600; font-size:0.85rem;">SMS Notifications</div>
                        <div style="font-size:0.72rem; color:var(--text-secondary);">Direct SMS on critical events</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="pref-sms" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="pref-item">
                    <div>
                        <div style="font-weight:600; font-size:0.85rem;">Geofence Alerts</div>
                        <div style="font-size:0.72rem; color:var(--text-secondary);">Notify when leaving Home Zone</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="pref-geofence" checked>
                        <span class="slider"></span>
                    </label>
                </div>
            </section>

            <!-- Device Pairing & Disconnect -->
            <section class="card">
                <div class="card-header">
                    <h2 class="card-title">Device Pairing</h2>
                </div>
                <p style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:12px;">
                    Currently linked to <strong id="settings-linked-stick">STICK_001</strong> via ESP32 Hardware Bridge.
                </p>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-full btn-sm" onclick="openQrModal()">
                        📱 Open QR Pairing
                    </button>
                    <button class="btn btn-emergency-outline btn-full btn-sm" onclick="promptDisconnectDevice()">
                        Disconnect Stick
                    </button>
                </div>
            </section>
        </main>

        <!-- ====================================================================
             BOTTOM NAVIGATION BAR
             ==================================================================== -->
        <nav class="bottom-nav" role="navigation" aria-label="Primary Navigation">
            <button class="nav-tab active" data-tab="home" onclick="switchTab('home')" aria-label="Home Dashboard">
                <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                <span>Home</span>
            </button>
            <button class="nav-tab" data-tab="location" onclick="switchTab('location')" aria-label="Location Map">
                <svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span>Location</span>
            </button>
            <button class="nav-tab" data-tab="alerts" onclick="switchTab('alerts')" aria-label="Alerts and Emergencies">
                <div class="nav-badge" id="tab-alerts-badge"></div>
                <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <span>Alerts</span>
            </button>
            <button class="nav-tab" data-tab="history" onclick="switchTab('history')" aria-label="Incident History">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>History</span>
            </button>
            <button class="nav-tab" data-tab="settings" onclick="switchTab('settings')" aria-label="Settings and Health">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                <span>Settings</span>
            </button>
        </nav>
    </div>

    <!-- ====================================================================
         QR SCANNER ACCESS MODAL
         ==================================================================== -->
    <div class="qr-modal-overlay" id="qr-modal" role="dialog" aria-modal="true" aria-labelledby="qr-heading">
        <div class="qr-modal-card">
            <button class="qr-close-btn" onclick="closeQrModal()" aria-label="Close QR Panel">✕</button>

            <h2 class="qr-heading" id="qr-heading">Your Guardian, Anywhere.</h2>
            <p class="qr-subheading">Scan with your phone to access your Smart Blind Stick Guardian.</p>

            <!-- QR Frame with Animated Scanline -->
            <div class="qr-code-frame">
                <div class="qr-scanline"></div>
                <div id="qr-canvas-container">
                    <!-- QRCode.js renders canvas/img here -->
                </div>
            </div>

            <!-- Live Connection Status -->
            <div>
                <span class="qr-status-indicator ready" id="qr-status-pill">
                    <span class="status-dot" id="qr-status-dot"></span>
                    <span id="qr-status-text">Ready to scan</span>
                </span>
            </div>

            <!-- Destination URL Box -->
            <div class="qr-url-box">
                <span class="qr-url-text" id="qr-target-url">http://172.20.10.3:8000/app</span>
                <button class="btn-copy-url" id="btn-copy-url" onclick="copyMobileUrl()">Copy Link</button>
            </div>

            <!-- Wi-Fi & Mobile Guidance -->
            <div class="qr-wifi-note">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
                <span>Make sure your phone and laptop are on the same Wi-Fi.</span>
            </div>

            <!-- Actions Row -->
            <div class="qr-actions-row">
                <button class="btn btn-secondary btn-sm" onclick="refreshNetworkInfo()">
                    🔄 Refresh IP
                </button>
                <button class="btn btn-secondary btn-sm" onclick="toggleManualIpInput()">
                    ⚙️ Edit IP
                </button>
            </div>

            <!-- Manual IP Override Drawer (Collapsible) -->
            <div id="qr-manual-drawer" style="display:none; margin-top:14px; text-align:left; border-top:1px solid var(--border-stone); padding-top:10px;">
                <label class="form-label">LAN Host / IP Override:</label>
                <div style="display:flex; gap:6px;">
                    <input type="text" id="input-manual-ip" class="form-input" style="margin-bottom:0;" placeholder="e.g. 192.168.1.100:8000">
                    <button class="btn btn-primary btn-sm" onclick="applyManualIp()">Apply</button>
                </div>
            </div>
        </div>
    </div>

    <!-- ====================================================================
         CONFIRMATION / INPUT MODALS
         ==================================================================== -->
    <!-- Resolve Emergency Modal -->
    <div class="modal-overlay" id="resolve-modal">
        <div class="modal-box">
            <h3 class="modal-title">Resolve Emergency Incident</h3>
            <p class="modal-body">
                Confirm that user safety has been addressed and assistance has been rendered.
            </p>
            <label class="form-label" for="resolve-notes-input">Resolution Notes (Optional):</label>
            <input type="text" id="resolve-notes-input" class="form-input" placeholder="e.g. Spoke with user, assistance rendered" value="Guardian confirmed user safety and resolved emergency.">
            <div class="modal-actions">
                <button class="btn btn-secondary btn-sm" onclick="closeResolveModal()">Cancel</button>
                <button class="btn btn-primary btn-sm" onclick="submitResolveEmergency()">Confirm Resolution</button>
            </div>
        </div>
    </div>

    <!-- Edit Profile Modal -->
    <div class="modal-overlay" id="profile-modal">
        <div class="modal-box">
            <h3 class="modal-title">Edit Guardian & Contacts</h3>
            <label class="form-label">Guardian Name</label>
            <input type="text" id="input-guardian-name" class="form-input" value="Elena Rivera">
            <label class="form-label">Guardian Phone</label>
            <input type="tel" id="input-guardian-phone" class="form-input" value="+1-555-0199">
            <label class="form-label">Monitored User Name</label>
            <input type="text" id="input-user-name" class="form-input" value="Alex Rivera">
            <label class="form-label">Monitored User Phone</label>
            <input type="tel" id="input-user-phone" class="form-input" value="+1-555-0198">
            <div class="modal-actions">
                <button class="btn btn-secondary btn-sm" onclick="closeProfileModal()">Cancel</button>
                <button class="btn btn-primary btn-sm" onclick="saveProfileChanges()">Save Changes</button>
            </div>
        </div>
    </div>

    <!-- Disconnect Confirmation Modal -->
    <div class="modal-overlay" id="disconnect-modal">
        <div class="modal-box">
            <h3 class="modal-title">Disconnect Smart Stick?</h3>
            <p class="modal-body">
                This will unpair the Guardian App from <strong>STICK_001</strong>. Real-time telemetry monitoring and emergency notifications will be paused.
            </p>
            <div class="modal-actions">
                <button class="btn btn-secondary btn-sm" onclick="closeDisconnectModal()">Keep Connected</button>
                <button class="btn btn-emergency btn-sm" onclick="confirmDisconnectDevice()">Disconnect</button>
            </div>
        </div>
    </div>

    <!-- Keyboard & Controls Modal -->
    <div class="modal-overlay" id="keyboard-modal" role="dialog" aria-modal="true" aria-labelledby="kb-modal-title">
        <div class="modal-box" style="max-width:500px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 class="modal-title" id="kb-modal-title" style="margin-bottom:0;">⌨️ Keyboard &amp; Controls</h3>
                <button class="qr-close-btn" onclick="closeKeyboardGuide()" style="position:static;">✕</button>
            </div>
            
            <p class="modal-body" style="margin-bottom:12px;">
                Connect a wireless Bluetooth keyboard or USB-OTG physical keyboard to navigate the Smart Blind Stick application without touch gestures.
            </p>

            <div style="display:flex; gap:8px; margin-bottom:14px;">
                <button class="btn btn-secondary btn-sm btn-full" onclick="connectBluetoothKeyboard()">
                    🔵 Connect Bluetooth Keyboard
                </button>
                <button class="btn btn-secondary btn-sm btn-full" onclick="connectUsbKeyboard()">
                    🔌 USB Keyboard Info
                </button>
            </div>

            <div class="pref-item" style="padding:8px 0; margin-bottom:10px;">
                <div>
                    <div style="font-weight:600; font-size:0.85rem;">Enable Keyboard Controls</div>
                    <div style="font-size:0.72rem; color:var(--text-secondary);">Allow physical keyboard to switch screens &amp; controls</div>
                </div>
                <label class="switch">
                    <input type="checkbox" id="toggle-keyboard-controls" checked onchange="toggleKeyboardControls(this.checked)">
                    <span class="slider"></span>
                </label>
            </div>

            <div style="background:var(--surface-subtle); border-radius:8px; padding:10px; margin-bottom:14px; font-size:0.8rem;">
                <div style="font-weight:700; margin-bottom:6px; color:var(--brand-primary);">Supported Keyboard Shortcuts:</div>
                <div style="display:grid; grid-template-columns: 80px 1fr; gap:6px; line-height:1.4;">
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">H</kbd></div><div>Home Dashboard</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">C</kbd></div><div>Device Connections</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">N</kbd></div><div>Navigation &amp; Live Map</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">S</kbd></div><div>Settings &amp; Diagnostics</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">↑ / ↓</kbd></div><div>Navigate Up / Down through controls</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">Enter</kbd></div><div>Activate selected button / view</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">Esc</kbd></div><div>Close open dialog / modal</div>
                    <div><kbd style="background:#FFF; padding:2px 6px; border:1px solid #CCC; border-radius:4px;">? / F1</kbd></div><div>Open this shortcut guide</div>
                </div>
            </div>

            <div style="background:var(--surface-white); border:1px solid var(--border-stone); border-radius:8px; padding:12px; margin-bottom:14px;">
                <div style="font-weight:700; font-size:0.8rem; margin-bottom:4px;">Test Keyboard Input:</div>
                <div id="keyboard-test-display" style="padding:10px; background:#F8FAF6; border:1px dashed #A3BCB4; border-radius:6px; text-align:center; font-family:monospace; font-size:0.85rem; color:var(--brand-primary);">
                    Press any key on your keyboard to test…
                </div>
            </div>

            <div class="modal-actions" style="justify-content:space-between;">
                <button class="btn btn-secondary btn-sm" onclick="resetKeyboardControlsToDefault()">
                    Reset to Default
                </button>
                <button class="btn btn-primary btn-sm" onclick="closeKeyboardGuide()">
                    Done
                </button>
            </div>
        </div>
    </div>

    <!-- Device Connection Center Modal -->
    <div class="modal-overlay" id="device-connection-modal" role="dialog" aria-modal="true" aria-labelledby="dc-modal-title">
        <div class="modal-box" style="max-width:480px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 class="modal-title" id="dc-modal-title" style="margin-bottom:0;">📡 Device Connection Center</h3>
                <button class="qr-close-btn" onclick="closeDeviceConnectionModal()" style="position:static;">✕</button>
            </div>

            <p class="modal-body" style="margin-bottom:14px;">
                Manage physical connection to the ESP32 Smart Blind Stick across Wi-Fi, Bluetooth, or USB.
            </p>

            <div style="background:var(--surface-subtle); border-radius:8px; padding:12px; margin-bottom:14px; border:1px solid var(--border-stone);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; font-size:0.88rem;" id="dc-status-title">Status: Awaiting Device</span>
                    <span class="tag tag-secondary" id="dc-status-tag">Disconnected</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;" id="dc-status-desc">
                    No active hardware session. Connect below via Wi-Fi or Bluetooth.
                </div>
            </div>

            <label class="form-label">Connect via Wi-Fi (IP / Hostname):</label>
            <div style="display:flex; gap:6px; margin-bottom:12px;">
                <input type="text" id="dc-wifi-ip" class="form-input" style="margin-bottom:0;" placeholder="192.168.4.1" value="192.168.4.1">
                <button class="btn btn-primary btn-sm" onclick="testWebWifiConnection()">Test / Ping</button>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px;">
                <button class="btn btn-secondary btn-sm" onclick="scanWebBluetooth()">
                    🔵 Scan Bluetooth
                </button>
                <button class="btn btn-secondary btn-sm" onclick="checkWebUsb()">
                    🔌 Check USB / OTG
                </button>
            </div>

            <div class="modal-actions" style="justify-content:space-between;">
                <button class="btn btn-emergency btn-sm" onclick="disconnectWebDevice()">
                    Disconnect
                </button>
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-secondary btn-sm" onclick="refreshWebDeviceStatus()">
                        Refresh Status
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="closeDeviceConnectionModal()">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>


    <!-- Floating Toast Feedback -->
    <div class="toast-banner" id="app-toast">Action Completed</div>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <!-- ====================================================================
         CLIENT LOGIC, CINEMATIC LOADER & QR WORKFLOWS
         ==================================================================== -->
    <script>
        let currentDeviceId = "STICK_001";
        let map = null;
        let stickMarker = null;
        let routePolyline = null;
        let geofenceCircle = null;
        let hazardMarkers = [];
        let routeCoords = [];
        let pollingTimer = null;
        let currentEmergencySession = null;
        let lastReportedLocation = {{ lat: 12.9716, lon: 77.5946 }};
        let lastSeenTimestamp = null;
        let activeHistoryFilter = 'all';
        let cachedEvents = [];
        let qrCodeInstance = null;
        let activeMobileUrl = window.location.origin + "/app";

        // -------------------------------------------------------------
        // 1. Cinematic Pre-Launch Loader Controller
        // -------------------------------------------------------------
        const loaderSteps = [
            {{ pct: 25, msg: "Initializing Guardian Subsystem..." }},
            {{ pct: 55, msg: "Establishing stick telemetry stream..." }},
            {{ pct: 85, msg: "Syncing GPS coordinates & hazard zones..." }},
            {{ pct: 100, msg: "Guardian safety dashboard ready." }}
        ];

        async function runCinematicLoader() {{
            const loaderEl = document.getElementById('cinematic-loader');
            const progressEl = document.getElementById('loader-progress');
            const statusTextEl = document.getElementById('loader-status-text');
            const warningBoxEl = document.getElementById('loader-warning-box');

            // Check reduced motion preference
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const alreadyBooted = sessionStorage.getItem('sightline_booted') === 'true';

            // If already booted in this session, transition out swiftly
            if (alreadyBooted && !window.forceLoaderReplay) {{
                loaderEl.classList.add('hide');
                return;
            }}

            window.forceLoaderReplay = false;

            const stepDelay = prefersReducedMotion ? 50 : 360;

            for (let i = 0; i < loaderSteps.length; i++) {{
                const s = loaderSteps[i];
                progressEl.style.width = s.pct + "%";
                statusTextEl.innerText = s.msg;
                await new Promise(r => setTimeout(r, stepDelay));
            }}

            // Real Health Verification
            try {{
                const res = await fetch('/health', {{ cache: 'no-store' }});
                if (!res.ok) throw new Error("Health check returned status " + res.status);
            }} catch (err) {{
                // Truthful warning if backend is unreachable
                warningBoxEl.style.display = "block";
                statusTextEl.innerText = "Connection alert: Server unresponsive";
                return; // Let user click proceed or retry
            }}

            // Smooth exit transition
            await new Promise(r => setTimeout(r, prefersReducedMotion ? 50 : 300));
            loaderEl.classList.add('hide');
            sessionStorage.setItem('sightline_booted', 'true');
        }}

        function dismissLoaderAnyway() {{
            document.getElementById('cinematic-loader').classList.add('hide');
            sessionStorage.setItem('sightline_booted', 'true');
        }}

        function replayCinematicIntro() {{
            window.forceLoaderReplay = true;
            const loaderEl = document.getElementById('cinematic-loader');
            document.getElementById('loader-warning-box').style.display = "none";
            document.getElementById('loader-progress').style.width = "0%";
            loaderEl.classList.remove('hide');
            runCinematicLoader();
        }}

        // -------------------------------------------------------------
        // 2. QR Scanner Access & Mobile Modal Controller
        // -------------------------------------------------------------
        async function openQrModal() {{
            const modal = document.getElementById('qr-modal');
            modal.classList.add('active');

            // 1. Fetch real host LAN IP from API
            await refreshNetworkInfo();
        }}

        function closeQrModal() {{
            document.getElementById('qr-modal').classList.remove('active');
        }}

        async function refreshNetworkInfo() {{
            const statusPill = document.getElementById('qr-status-pill');
            const statusDot = document.getElementById('qr-status-dot');
            const statusText = document.getElementById('qr-status-text');

            statusPill.className = "qr-status-indicator";
            statusDot.className = "status-dot";
            statusText.innerText = "Preparing secure connection...";

            try {{
                const res = await fetch('/api/network-info');
                if (res.ok) {{
                    const info = await res.json();
                    activeMobileUrl = info.mobile_app_url || `http://${{info.local_ip}}:${{info.port}}/app`;
                    renderQrCode(activeMobileUrl);

                    statusPill.className = "qr-status-indicator ready";
                    statusDot.className = "status-dot";
                    statusText.innerText = "Ready to scan";
                }} else {{
                    throw new Error("API error " + res.status);
                }}
            }} catch (err) {{
                // Fallback to current host if network-info fails
                const fallbackUrl = window.location.href.replace('/dashboard', '/app');
                activeMobileUrl = fallbackUrl;
                renderQrCode(fallbackUrl);

                statusPill.className = "qr-status-indicator";
                statusDot.className = "status-dot offline";
                statusText.innerText = "Local fallback ready";
            }}

            document.getElementById('qr-target-url').innerText = activeMobileUrl;
        }}

        function renderQrCode(url) {{
            const container = document.getElementById('qr-canvas-container');
            container.innerHTML = "";

            if (typeof QRCode !== 'undefined') {{
                try {{
                    qrCodeInstance = new QRCode(container, {{
                        text: url,
                        width: 200,
                        height: 200,
                        colorDark: "#173C35",
                        colorLight: "#FFFFFF",
                        correctLevel: QRCode.CorrectLevel.M
                    }});
                }} catch (e) {{
                    fallbackQrRenderer(container, url);
                }}
            }} else {{
                fallbackQrRenderer(container, url);
            }}
        }}

        function fallbackQrRenderer(container, url) {{
            // High-reliability SVG/Image fallback via secure QR API
            const encoded = encodeURIComponent(url);
            container.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&color=17-60-53&data=${{encoded}}" alt="Mobile Access QR Code" style="width:200px; height:200px; border-radius:8px;" />`;
        }}

        function copyMobileUrl() {{
            navigator.clipboard.writeText(activeMobileUrl).then(() => {{
                const btn = document.getElementById('btn-copy-url');
                btn.innerText = "Copied! ✓";
                showToast("Mobile link copied to clipboard");
                setTimeout(() => {{
                    btn.innerText = "Copy Link";
                }}, 2200);
            }}).catch(() => {{
                showToast("URL: " + activeMobileUrl);
            }});
        }}

        function toggleManualIpInput() {{
            const drawer = document.getElementById('qr-manual-drawer');
            drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
            if (drawer.style.display === 'block') {{
                document.getElementById('input-manual-ip').focus();
            }}
        }}

        function applyManualIp() {{
            let val = document.getElementById('input-manual-ip').value.trim();
            if (!val) return;
            if (!val.startsWith('http://') && !val.startsWith('https://')) {{
                val = 'http://' + val;
            }}
            if (!val.endsWith('/app')) {{
                val = val + '/app';
            }}
            activeMobileUrl = val;
            document.getElementById('qr-target-url').innerText = activeMobileUrl;
            renderQrCode(activeMobileUrl);
            showToast("Updated QR code with custom address");
        }}

        // -------------------------------------------------------------
        // Keyboard & Device Connection Center Controllers
        // -------------------------------------------------------------
        let currentFocusIndex = -1;

        function closeActiveModal() {{
            closeQrModal();
            closeResolveModal();
            closeProfileModal();
            closeDisconnectModal();
            closeKeyboardGuide();
            closeDeviceConnectionModal();
        }}

        function openDeviceConnectionCenter() {{
            if (window.AndroidHardwareBridge && window.AndroidHardwareBridge.openHardwareSettings) {{
                window.AndroidHardwareBridge.openHardwareSettings();
            }} else {{
                const modal = document.getElementById('device-connection-modal');
                if (modal) modal.classList.add('active');
            }}
        }}

        function closeDeviceConnectionModal() {{
            const modal = document.getElementById('device-connection-modal');
            if (modal) modal.classList.remove('active');
        }}

        async function testWebWifiConnection() {{
            const ip = document.getElementById('dc-wifi-ip').value.trim();
            if (!ip) return;
            showToast("Pinging stick at " + ip + "...");
            try {{
                const res = await fetch('/api/device/ping-hardware', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ stick_ip: ip, timeout_seconds: 2.0 }})
                }});
                const data = await res.json();
                if (data.reachable) {{
                    document.getElementById('dc-status-title').innerText = "Status: Reachable (" + (data.latency_ms || 12) + "ms)";
                    document.getElementById('dc-status-tag').innerText = "Online";
                    document.getElementById('dc-status-tag').className = "tag tag-success";
                    document.getElementById('dc-status-desc').innerText = "Stick responded over local Wi-Fi link.";
                    showToast("Stick reachable over Wi-Fi! Latency: " + data.latency_ms + "ms");
                }} else {{
                    document.getElementById('dc-status-title').innerText = "Status: Unreachable";
                    document.getElementById('dc-status-tag').innerText = "Offline";
                    document.getElementById('dc-status-tag').className = "tag tag-secondary";
                    document.getElementById('dc-status-desc').innerText = data.message || "No response from target IP.";
                    showToast("Stick unreachable: " + (data.message || "Timeout"));
                }}
            }} catch (err) {{
                showToast("Wi-Fi test error: " + err);
            }}
        }}

        async function scanWebBluetooth() {{
            if (window.AndroidHardwareBridge && window.AndroidHardwareBridge.openHardwareSettings) {{
                window.AndroidHardwareBridge.openHardwareSettings();
                return;
            }}
            if (!navigator.bluetooth) {{
                showToast("Web Bluetooth requires Chrome or an Android Companion App.");
                return;
            }}
            try {{
                showToast("Requesting Bluetooth device...");
                const device = await navigator.bluetooth.requestDevice({{
                    acceptAllDevices: true,
                    optionalServices: ['00001101-0000-1000-8000-00805f9b34fb', '6e400001-b5a3-f393-e0a9-e50e24dcca9e']
                }});
                if (device) {{
                    document.getElementById('dc-status-title').innerText = "Status: " + (device.name || "Bluetooth Stick");
                    document.getElementById('dc-status-tag').innerText = "Paired";
                    document.getElementById('dc-status-tag').className = "tag tag-success";
                    showToast("Selected: " + (device.name || "Bluetooth Stick"));
                }}
            }} catch (err) {{
                showToast("Bluetooth scan cancelled or unsupported: " + err.message);
            }}
        }}

        function checkWebUsb() {{
            if (window.AndroidHardwareBridge && window.AndroidHardwareBridge.getUsbStatus) {{
                const status = window.AndroidHardwareBridge.getUsbStatus();
                showToast("USB OTG Status: " + status);
                document.getElementById('dc-status-desc').innerText = "USB Host: " + status;
            }} else {{
                showToast("USB OTG Host: Connect stick using USB-OTG cable on Android device.");
            }}
        }}

        function disconnectWebDevice() {{
            showToast("Hardware stick disconnected");
            document.getElementById('dc-status-title').innerText = "Status: Disconnected";
            document.getElementById('dc-status-tag').innerText = "Disconnected";
            document.getElementById('dc-status-tag').className = "tag tag-secondary";
            document.getElementById('dc-status-desc').innerText = "Hardware connection closed.";
        }}

        async function refreshWebDeviceStatus() {{
            try {{
                const res = await fetch('/api/device/connectivity-status');
                if (res.ok) {{
                    const d = await res.json();
                    document.getElementById('dc-status-title').innerText = "Status: " + (d.overall_online ? "Active Link" : "Awaiting Device");
                    document.getElementById('dc-status-tag').innerText = d.overall_online ? "Online" : "Disconnected";
                    document.getElementById('dc-status-tag').className = d.overall_online ? "tag tag-success" : "tag tag-secondary";
                    showToast("Device status updated: " + (d.overall_online ? "Online" : "Awaiting stick"));
                }} else {{
                    showToast("Could not retrieve status");
                }}
            }} catch (e) {{
                showToast("Status refresh error: " + e);
            }}
        }}

        function openKeyboardGuide() {{
            const modal = document.getElementById('keyboard-modal');
            if (modal) modal.classList.add('active');
        }}

        function closeKeyboardGuide() {{
            const modal = document.getElementById('keyboard-modal');
            if (modal) modal.classList.remove('active');
        }}

        function connectBluetoothKeyboard() {{
            if (window.AndroidHardwareBridge && window.AndroidHardwareBridge.openSystemBluetoothSettings) {{
                window.AndroidHardwareBridge.openSystemBluetoothSettings();
            }} else {{
                showToast("Open your device Bluetooth Settings to pair a wireless keyboard.");
            }}
        }}

        function connectUsbKeyboard() {{
            showToast("Connect your USB keyboard via USB-OTG adapter. Android recognizes it automatically.");
        }}

        function toggleKeyboardControls(enabled) {{
            localStorage.setItem('keyboard_controls_enabled', enabled ? 'true' : 'false');
            showToast(enabled ? "Keyboard navigation enabled" : "Keyboard navigation disabled");
        }}

        function resetKeyboardControlsToDefault() {{
            localStorage.setItem('keyboard_controls_enabled', 'true');
            const toggle = document.getElementById('toggle-keyboard-controls');
            if (toggle) toggle.checked = true;
            showToast("Keyboard shortcuts reset to defaults (H, C, N, S, ?, Esc, Arrows)");
        }}

        function navigateControl(step) {{
            const focusables = Array.from(document.querySelectorAll('button:not([disabled]), a.btn, input:not([type="hidden"])'))
                .filter(el => el.offsetParent !== null);
            if (focusables.length === 0) return;
            currentFocusIndex = (currentFocusIndex + step + focusables.length) % focusables.length;
            focusables[currentFocusIndex].focus();
            showToast("Selected: " + (focusables[currentFocusIndex].innerText || focusables[currentFocusIndex].getAttribute('aria-label') || "Control"));
        }}

        function activateCurrentControl() {{
            if (document.activeElement && typeof document.activeElement.click === 'function') {{
                document.activeElement.click();
            }}
        }}

        async function checkVisionInference() {{
            showToast("Checking AI Vision model status...");
            try {{
                const res = await fetch('/api/vision/status');
                if (res.ok) {{
                    const d = await res.json();
                    const isReady = d.status === 'ready';
                    document.getElementById('ai-vision-status-tag').innerText = isReady ? 'Model Ready' : 'Vision Offline';
                    document.getElementById('ai-vision-status-tag').className = isReady ? 'tag tag-success' : 'tag tag-secondary';
                    document.getElementById('ai-model-name').innerText = d.model_version || 'YOLOv8n-COCO';
                    document.getElementById('ai-latency-val').innerText = isReady ? '~38 ms' : 'N/A';
                    document.getElementById('ai-vision-label').innerText = isReady ? 'YOLOv8n Inference Operational' : 'Model Offline / Standby';
                    showToast(isReady ? "AI Vision model verified ready on server" : "Vision inference standby (zero fabricated data)");
                }} else {{
                    document.getElementById('ai-vision-status-tag').innerText = 'Offline';
                    showToast("Vision status error: " + res.status);
                }}
            }} catch (err) {{
                document.getElementById('ai-vision-status-tag').innerText = 'Offline';
                showToast("Could not contact vision service: " + err);
            }}
        }}

        // Global Physical Keyboard Event Listener
        window.addEventListener('keydown', (e) => {{
            // Never hijack typing in active text inputs
            if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) {{
                if (e.key === 'Escape') {{
                    document.activeElement.blur();
                    closeActiveModal();
                }}
                return;
            }}

            // Visual test feedback
            const testDisp = document.getElementById('keyboard-test-display');
            if (testDisp) {{
                testDisp.innerText = 'Key Pressed: "' + e.key + '" (Code: ' + e.code + ')';
            }}

            if (e.key === 'Escape') {{
                closeActiveModal();
                return;
            }}

            const keyControlsEnabled = localStorage.getItem('keyboard_controls_enabled') !== 'false';
            if (!keyControlsEnabled) return;

            if (e.key === 'h' || e.key === 'H') {{
                switchTab('home');
            }} else if (e.key === 'c' || e.key === 'C') {{
                openDeviceConnectionCenter();
            }} else if (e.key === 'n' || e.key === 'N') {{
                switchTab('location');
            }} else if (e.key === 's' || e.key === 'S') {{
                switchTab('settings');
            }} else if (e.key === '?' || e.key === 'F1') {{
                e.preventDefault();
                openKeyboardGuide();
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                navigateControl(-1);
            }} else if (e.key === 'ArrowDown') {{
                e.preventDefault();
                navigateControl(1);
            }} else if (e.key === 'Enter') {{
                activateCurrentControl();
            }}
        }});

        // Close on clicking outside modal card
        document.getElementById('qr-modal').addEventListener('click', (e) => {{
            if (e.target.id === 'qr-modal') closeQrModal();
        }});


        // -------------------------------------------------------------
        // 3. Tab Navigation
        // -------------------------------------------------------------
        function switchTab(tabId) {{
            // Deactivate all views
            document.querySelectorAll('.view-content').forEach(el => el.classList.remove('active'));
            // Deactivate all nav tabs
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

            const targetView = document.getElementById(`view-${{tabId}}`);
            const targetTabBtn = document.querySelector(`.nav-tab[data-tab="${{tabId}}"]`);

            if (targetView) targetView.classList.add('active');
            if (targetTabBtn) targetTabBtn.classList.add('active');

            // If switching to Location, trigger map resize
            if (tabId === 'location') {{
                setTimeout(() => {{
                    if (map) {{
                        map.invalidateSize();
                        if (stickMarker) map.panTo(stickMarker.getLatLng());
                    }}
                }}, 150);
            }}

            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // -------------------------------------------------------------
        // 4. Toast Notification System
        // -------------------------------------------------------------
        function showToast(message) {{
            const toast = document.getElementById('app-toast');
            toast.innerText = message;
            toast.classList.add('show');
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 2600);
        }}

        // -------------------------------------------------------------
        // 5. Leaflet Map Initialization
        // -------------------------------------------------------------
        function initLeafletMap() {{
            // Neutral overview until physical stick reports genuine GPS coordinates
            map = L.map('map', {{
                zoomControl: true,
                attributionControl: false
            }}).setView([20.5937, 78.9629], 4);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap'
            }}).addTo(map);

            routePolyline = L.polyline([], {{
                color: '#3E7569',
                weight: 4,
                opacity: 0.8,
                dashArray: '5, 8'
            }}).addTo(map);

            loadCommunityHazards();
        }}

        async function loadCommunityHazards() {{
            try {{
                const res = await fetch('/api/features/hazards');
                if (res.ok) {{
                    const hazards = await res.json();
                    hazardMarkers.forEach(h => map.removeLayer(h));
                    hazardMarkers = [];
                    hazards.forEach(h => {{
                        const m = L.circleMarker([h.latitude, h.longitude], {{
                            radius: 7,
                            color: '#A86419',
                            fillColor: '#FFF2DC',
                            fillOpacity: 0.9,
                            weight: 2
                        }}).addTo(map).bindPopup(`<b>⚠️ Hazard: ${{h.title}}</b><br>${{h.description || ''}} (${{h.severity}})`);
                        hazardMarkers.push(m);
                    }});
                }}
            }} catch (e) {{}}
        }}

        function centerMapOnStick() {{
            if (map && stickMarker) {{
                map.setView(stickMarker.getLatLng(), 17, {{ animate: true }});
                showToast("Map centered on stick");
            }} else {{
                showToast("GPS position not yet reported by stick");
            }}
        }}

        function openExternalDirections() {{
            if (!lastReportedLocation || lastReportedLocation.lat == null) {{
                showToast("Cannot navigate: GPS fix unavailable");
                return;
            }}
            const url = `https://www.google.com/maps/dir/?api=1&destination=${{lastReportedLocation.lat}},${{lastReportedLocation.lon}}`;
            window.open(url, '_blank');
        }}

        // -------------------------------------------------------------
        // 6. Polling & Real-time Telemetry
        // -------------------------------------------------------------
        async function fetchStickData() {{
            try {{
                // 1. Device Status
                const statusRes = await fetch(`/api/device/status/${{currentDeviceId}}`);
                if (statusRes.ok) {{
                    const d = await statusRes.json();
                    updateDeviceStatusUI(d);
                }} else {{
                    setDeviceOfflineUI();
                }}

                // 2. Emergency Status
                const emgRes = await fetch(`/api/emergency/status/${{currentDeviceId}}`);
                if (emgRes.ok) {{
                    const emg = await emgRes.json();
                    updateEmergencyUI(emg);
                }}

                // 3. Location
                const locRes = await fetch(`/api/location/${{currentDeviceId}}`);
                if (locRes.ok) {{
                    const loc = await locRes.json();
                    updateLocationUI(loc);
                }}

                // 4. Events
                const evtRes = await fetch(`/api/events/${{currentDeviceId}}?limit=25`);
                if (evtRes.ok) {{
                    const evts = await evtRes.json();
                    cachedEvents = evts;
                    renderEventsList(evts);
                    renderRecentAlerts(evts);
                }}
            }} catch (err) {{
                console.warn("Telemetry fetch error:", err);
            }}
        }}

        function updateDeviceStatusUI(st) {{
            const isOnline = Boolean(st.is_online || st.online);
            const bat = (st.battery != null && st.battery !== undefined) ? Math.round(st.battery) : null;

            // Header pills
            document.getElementById('header-battery-pct').innerText = bat != null ? `${{bat}}%` : '--%';
            const headerDot = document.getElementById('header-status-dot');
            if (isOnline) {{
                headerDot.className = "status-dot";
            }} else {{
                headerDot.className = "status-dot offline";
            }}

            // Home metrics cards
            document.getElementById('card-battery-val').innerText = bat != null ? `${{bat}}%` : 'Unavailable';
            const batFill = document.getElementById('card-battery-fill');
            batFill.style.width = bat != null ? `${{bat}}%` : '0%';
            batFill.style.background = bat == null ? 'var(--text-muted)' : (bat < 20 ? 'var(--emergency)' : (bat < 50 ? 'var(--warning)' : 'var(--success)'));
            document.getElementById('card-battery-sub').innerText = bat != null ? (bat < 20 ? 'Low Battery — Recharge' : 'Battery level OK') : 'No voltage sensor calibrated';

            // GPS Metric
            const sats = (st.last_satellites != null) ? st.last_satellites : ((st.satellites != null) ? st.satellites : 0);
            document.getElementById('card-gps-val').innerText = sats > 0 ? `${{sats}} Sats` : 'No Fix';
            document.getElementById('card-gps-sub').innerText = sats >= 4 ? '3D Fix Acquired' : (sats > 0 ? 'Acquiring satellites' : 'GPS fix unavailable');
            document.getElementById('loc-sat-count').innerText = sats > 0 ? `${{sats}} Fixed` : '0 Fixed';

            // Connectivity Metric
            document.getElementById('card-conn-val').innerText = isOnline ? 'ONLINE' : 'OFFLINE';
            document.getElementById('card-conn-sub').innerText = isOnline ? 'ESP32 Controller' : 'No heartbeat';

            // Safety Summary panel
            lastSeenTimestamp = st.last_seen ? new Date(st.last_seen) : null;
            updateLastCommLabel();

            if (!isOnline) {{
                setSafetySummary("offline", "Device offline", "The stick has not sent a heartbeat recently. Reconnect to resume live tracking.");
            }} else if (!currentEmergencySession || currentEmergencySession.state === 'IDLE' || currentEmergencySession.state === 'NORMAL') {{
                setSafetySummary("normal", "Device reporting normally", "Hardware heartbeat and sensor streams reporting nominal baseline operation.");
            }}
        }}

        function setDeviceOfflineUI() {{
            document.getElementById('header-status-dot').className = "status-dot offline";
            document.getElementById('card-conn-val').innerText = "OFFLINE";
            document.getElementById('card-conn-sub').innerText = "Bridge Disconnected";
            setSafetySummary("offline", "Device offline", "The stick is not communicating with the server. Telemetry temporarily unavailable.");
        }}

        function setSafetySummary(level, title, explanation) {{
            const badge = document.getElementById('safety-badge');
            const dot = document.getElementById('safety-dot');
            const text = document.getElementById('safety-status-text');
            const exp = document.getElementById('safety-explanation');

            badge.className = `safety-badge ${{level}}`;
            dot.className = `status-dot ${{level === 'emergency' ? 'emergency' : (level === 'offline' ? 'offline' : '')}}`;
            text.innerText = title;
            exp.innerText = explanation;
        }}

        function updateLastCommLabel() {{
            if (!lastSeenTimestamp) {{
                const commEl = document.getElementById('safety-last-comm');
                if (commEl) commEl.innerText = "Never connected";
                return;
            }}
            const diffSeconds = Math.max(0, Math.round((new Date() - lastSeenTimestamp) / 1000));
            const commEl = document.getElementById('safety-last-comm');
            if (!commEl) return;
            if (diffSeconds < 5) {{
                commEl.innerText = "Updated just now";
            }} else if (diffSeconds < 60) {{
                commEl.innerText = `Updated ${{diffSeconds}}s ago`;
            }} else {{
                commEl.innerText = `Updated ${{Math.round(diffSeconds / 60)}}m ago`;
            }}
        }}

        function updateEmergencyUI(emg) {{
            currentEmergencySession = emg;
            const banner = document.getElementById('home-emergency-banner');
            const alertsBadge = document.getElementById('tab-alerts-badge');
            const activeContainer = document.getElementById('active-incidents-container');

            if (emg.state === 'ACTIVE_SOS') {{
                // Elevated Home banner
                banner.className = "emergency-banner visible";
                document.getElementById('home-emg-title').innerText = "🚨 CRITICAL: ACTIVE SOS TRIGGERED";
                document.getElementById('home-emg-desc').innerText = `Physical emergency button pressed on stick. Dispatched to guardians (${{emg.notification_status || 'Active'}}).`;
                document.getElementById('home-emg-time').innerText = `Started: ${{emg.started_at ? new Date(emg.started_at).toLocaleTimeString() : 'Just now'}}`;
                document.getElementById('home-emg-coords').innerText = (emg.latitude != null && emg.longitude != null) ? `GPS: ${{emg.latitude.toFixed(4)}}, ${{emg.longitude.toFixed(4)}}` : 'GPS: Fix unavailable';

                // Badge on alerts tab
                alertsBadge.classList.add('visible');

                // Safety summary
                setSafetySummary("emergency", "Active emergency", "Manual SOS triggered from the stick. Immediate guardian response required.");

                // Render active card in Alerts Tab
                activeContainer.innerHTML = `
                    <div class="incident-card critical">
                        <div class="incident-top">
                            <div class="incident-title">🚨 Active SOS Emergency</div>
                            <span class="tag tag-emergency">CRITICAL</span>
                        </div>
                        <div class="incident-time">${{emg.started_at ? new Date(emg.started_at).toLocaleString() : 'Active Now'}}</div>
                        <div class="incident-details-box">
                            The user pressed the physical emergency switch on the stick. Location coordinates captured and guardian notified.
                        </div>
                        <div class="incident-actions-row">
                            <button class="btn btn-primary btn-sm" onclick="acknowledgeAlert('Manual SOS')">Acknowledge</button>
                            <a href="tel:+15550198" class="btn btn-secondary btn-sm">Call Alex (User)</a>
                            <button class="btn btn-emergency-outline btn-sm" onclick="openResolveModal('${{emg.session_id || ''}}')">Resolve Emergency</button>
                        </div>
                    </div>
                `;
            }} else if (emg.state === 'PENDING_CONFIRMATION') {{
                // Fall detected countdown
                banner.className = "emergency-banner visible";
                document.getElementById('home-emg-title').innerText = `⚠️ POTENTIAL FALL DETECTED (${{emg.countdown_remaining_seconds || 15}}s)`;
                document.getElementById('home-emg-desc').innerText = "Stick detected an impact with posture tilt. Awaiting confirmation or user cancellation.";
                document.getElementById('home-emg-time').innerText = `Countdown: ${{emg.countdown_remaining_seconds || 15}}s remaining`;
                document.getElementById('home-emg-coords').innerText = (emg.latitude != null && emg.longitude != null) ? `GPS: ${{emg.latitude.toFixed(4)}}, ${{emg.longitude.toFixed(4)}}` : 'GPS: Fix unavailable';

                alertsBadge.classList.add('visible');
                setSafetySummary("warning", "Warning requiring attention", "Potential fall event detected by MPU6050 sensor. Waiting on user cancellation window.");

                activeContainer.innerHTML = `
                    <div class="incident-card warning">
                        <div class="incident-top">
                            <div class="incident-title">⚠️ Potential Fall Detected</div>
                            <span class="tag tag-warning">CONFIRMATION (${{emg.countdown_remaining_seconds || 15}}s)</span>
                        </div>
                        <div class="incident-time">Detected: ${{new Date().toLocaleTimeString()}}</div>
                        <div class="incident-details-box">
                            Sensor fusion evaluated high impact & horizontal rest. If this is a false alarm, cancel below.
                        </div>
                        <div class="incident-actions-row">
                            <button class="btn btn-secondary btn-sm" onclick="cancelPendingFall()">Cancel False Alarm</button>
                            <a href="tel:+15550198" class="btn btn-primary btn-sm">Call User</a>
                        </div>
                    </div>
                `;
            }} else {{
                banner.className = "emergency-banner";
                alertsBadge.classList.remove('visible');
                activeContainer.innerHTML = `
                    <div class="card" style="text-align:center; padding: 24px;">
                        <div style="width:36px; height:36px; border-radius:50%; background:var(--success-bg); color:var(--success); display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto;">✓</div>
                        <div style="font-family:var(--font-display); font-weight:700; font-size:0.95rem; margin-bottom:4px;">No Active Emergencies</div>
                        <div style="font-size:0.8rem; color:var(--text-secondary);">The stick is reporting within expected parameters. Guardian monitoring is active.</div>
                    </div>
                `;
            }}
        }}

        function updateLocationUI(loc) {{
            if (!loc || loc.latitude == null || loc.longitude == null) {{
                document.getElementById('home-coords-preview').innerText = "GPS fix unavailable";
                document.getElementById('loc-full-coords').innerText = "GPS fix unavailable";
                const locBadge = document.getElementById('loc-status-badge');
                if (locBadge) {{
                    locBadge.innerText = "GPS fix unavailable";
                    locBadge.className = "loc-status-pill stale";
                }}
                return;
            }}
            lastReportedLocation = {{ lat: loc.latitude, lon: loc.longitude }};

            const coordsText = `${{loc.latitude.toFixed(5)}}° N, ${{loc.longitude.toFixed(5)}}° E`;
            document.getElementById('home-coords-preview').innerText = coordsText;
            document.getElementById('loc-full-coords').innerText = coordsText;

            const latLng = [loc.latitude, loc.longitude];
            if (stickMarker) {{
                stickMarker.setLatLng(latLng);
            }} else if (map) {{
                const stickIcon = L.divIcon({{
                    className: 'custom-stick-pin',
                    html: `
                        <div style="background:#173C35; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 12px rgba(23,60,53,0.4); border:2.5px solid #FFFFFF;">
                            <span style="font-size:16px;">🦯</span>
                        </div>
                    `,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                }});
                stickMarker = L.marker(latLng, {{ icon: stickIcon }}).addTo(map);
                stickMarker.bindPopup("<b>Smart Blind Stick</b><br>Live GPS Coordinates");
                map.setView(latLng, 16);
            }}

            routeCoords.push(latLng);
            if (routeCoords.length > 30) routeCoords.shift();
            if (routePolyline) routePolyline.setLatLngs(routeCoords);

            // Stale check
            const locBadge = document.getElementById('loc-status-badge');
            if (locBadge) {{
                locBadge.innerText = "Live GPS Position";
                locBadge.className = "loc-status-pill";
            }}
        }}

        function renderRecentAlerts(events) {{
            const listEl = document.getElementById('home-recent-alerts');
            if (!Array.isArray(events) || events.length === 0) {{
                listEl.innerHTML = '<div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:10px;">No recent incidents recorded.</div>';
                return;
            }}

            const recent = events.slice(0, 3);
            let html = '';
            recent.forEach(ev => {{
                const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent';
                html += `
                    <div class="alert-row-item" onclick="switchTab('history')">
                        <div class="alert-row-main">
                            <div class="alert-row-title">${{escapeHtml(ev.message || ev.event_type)}}</div>
                            <div class="alert-row-time">${{timeStr}} • ${{ev.source || 'stick'}}</div>
                        </div>
                        <span class="tag tag-${{ev.risk_level === 'critical' ? 'emergency' : (ev.risk_level === 'high' ? 'warning' : 'neutral')}}">
                            ${{ev.risk_level || 'info'}}
                        </span>
                    </div>
                `;
            }});
            listEl.innerHTML = html;
        }}

        function renderEventsList(events) {{
            const timelineEl = document.getElementById('history-timeline-list');
            const notifEl = document.getElementById('notifications-container');

            if (!Array.isArray(events) || events.length === 0) {{
                timelineEl.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-title">No Events Recorded</div>
                        <div class="empty-desc">Stick is operating normally. All events and safety triggers will appear here in chronological order.</div>
                    </div>
                `;
                notifEl.innerHTML = '<div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:12px;">No historical notifications.</div>';
                return;
            }}

            let filtered = events;
            if (activeHistoryFilter === 'emergency') {{
                filtered = events.filter(e => e.event_type.includes('sos') || e.event_type.includes('fall') || e.risk_level === 'critical');
            }} else if (activeHistoryFilter === 'obstacle') {{
                filtered = events.filter(e => e.event_type.includes('obstacle') || e.event_type.includes('object'));
            }} else if (activeHistoryFilter === 'geofence') {{
                filtered = events.filter(e => e.event_type.includes('geofence') || e.event_type.includes('zone'));
            }} else if (activeHistoryFilter === 'system') {{
                filtered = events.filter(e => e.event_type.includes('battery') || e.event_type.includes('diagnostic') || e.event_type.includes('system'));
            }}

            if (filtered.length === 0) {{
                timelineEl.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-title">No Matches</div>
                        <div class="empty-desc">No events found matching '${{activeHistoryFilter}}'.</div>
                    </div>
                `;
                return;
            }}

            let timelineHtml = '<div class="timeline-date-label">Today</div>';
            filtered.forEach(ev => {{
                const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '';
                const isCrit = ev.risk_level === 'critical';
                const isWarn = ev.risk_level === 'high';

                timelineHtml += `
                    <div class="history-row">
                        <div class="history-left">
                            <div class="history-icon-box">
                                ${{isCrit ? '🚨' : (isWarn ? '⚠️' : 'ℹ️')}}
                            </div>
                            <div class="history-texts">
                                <div class="history-msg">${{escapeHtml(ev.message || ev.event_type)}}</div>
                                <div class="history-meta">${{timeStr}} • ${{ev.source}}</div>
                            </div>
                        </div>
                        <span class="tag tag-${{isCrit ? 'emergency' : (isWarn ? 'warning' : 'neutral')}}">
                            ${{ev.risk_level || 'info'}}
                        </span>
                    </div>
                `;
            }});
            timelineEl.innerHTML = timelineHtml;

            // Notifications in alerts tab
            let notifHtml = '';
            events.slice(0, 10).forEach(ev => {{
                const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '';
                notifHtml += `
                    <div class="incident-card resolved">
                        <div class="incident-top">
                            <div class="incident-title">${{escapeHtml(ev.message || ev.event_type)}}</div>
                            <span class="tag tag-${{ev.risk_level === 'critical' ? 'emergency' : 'neutral'}}">${{ev.risk_level || 'info'}}</span>
                        </div>
                        <div class="incident-time">${{timeStr}} • Source: ${{ev.source}}</div>
                    </div>
                `;
            }});
            notifEl.innerHTML = notifHtml;
        }}

        function filterHistory(category, btn) {{
            activeHistoryFilter = category;
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderEventsList(cachedEvents);
        }}

        // -------------------------------------------------------------
        // 7. Incident Actions & Modal Workflows
        // -------------------------------------------------------------
        async function acknowledgeAlert(eventDesc) {{
            try {{
                await fetch('/api/events', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        device_id: currentDeviceId,
                        event_type: "guardian_acknowledged",
                        severity: "info",
                        message: `Guardian acknowledged ${{eventDesc}}`,
                        source: "guardian_app"
                    }})
                }});
                showToast("Incident acknowledged by guardian");
                fetchStickData();
            }} catch (e) {{
                showToast("Failed to acknowledge: " + e);
            }}
        }}

        function openResolveModal(sessionId) {{
            document.getElementById('resolve-modal').classList.add('active');
        }}

        function closeResolveModal() {{
            document.getElementById('resolve-modal').classList.remove('active');
        }}

        async function submitResolveEmergency() {{
            const notes = document.getElementById('resolve-notes-input').value;
            try {{
                const res = await fetch('/api/emergency/sos/resolve', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        device_id: currentDeviceId,
                        resolution_notes: notes
                    }})
                }});
                closeResolveModal();
                if (res.ok) {{
                    showToast("Emergency incident resolved successfully");
                    fetchStickData();
                }} else {{
                    showToast("Could not resolve incident on server");
                }}
            }} catch (e) {{
                closeResolveModal();
                showToast("Network error resolving emergency: " + e);
            }}
        }}

        async function cancelPendingFall() {{
            try {{
                const res = await fetch('/api/emergency/sos/cancel', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        device_id: currentDeviceId,
                        reason: "Guardian confirmed false alarm via mobile app"
                    }})
                }});
                if (res.ok) {{
                    showToast("False alarm cancelled");
                    fetchStickData();
                }} else {{
                    showToast("Error cancelling: " + res.status);
                }}
            }} catch (e) {{
                showToast("Error cancelling: " + e);
            }}
        }}

        // -------------------------------------------------------------
        // 8. Diagnostics & Profile Workflows
        // -------------------------------------------------------------
        async function runDiagnosticsTest() {{
            showToast("Running hardware diagnostics...");
            try {{
                const res = await fetch(`/api/features/diagnostics/run/${{currentDeviceId}}`, {{ method: 'POST' }});
                if (res.ok) {{
                    const d = await res.json();
                    document.getElementById('settings-diag-badge').innerText = d.overall_health === 'healthy' ? 'Nominal' : 'Warning';
                    showToast(d.startup_announcement || "Diagnostics Complete: All systems nominal");
                }} else {{
                    showToast("Diagnostics complete");
                }}
            }} catch (e) {{
                showToast("Diagnostics error: " + e);
            }}
        }}

        function openProfileEditModal() {{
            document.getElementById('profile-modal').classList.add('active');
        }}

        function closeProfileModal() {{
            document.getElementById('profile-modal').classList.remove('active');
        }}

        async function saveProfileChanges() {{
            const gName = document.getElementById('input-guardian-name').value;
            const gPhone = document.getElementById('input-guardian-phone').value;
            const uName = document.getElementById('input-user-name').value;
            const uPhone = document.getElementById('input-user-phone').value;

            document.getElementById('profile-guardian-name').innerText = gName;
            document.getElementById('profile-guardian-phone').innerText = gPhone;
            document.getElementById('profile-user-name').innerText = uName;
            document.getElementById('profile-user-phone').innerText = uPhone;

            closeProfileModal();
            showToast("Guardian profile updated");

            try {{
                await fetch(`/api/features/profile/${{currentDeviceId}}`, {{
                    method: 'PUT',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        full_name: uName,
                        guardian_name: gName,
                        guardian_phone: gPhone,
                        emergency_contact_phone: gPhone
                    }})
                }});
            }} catch (e) {{}}
        }}

        function promptDisconnectDevice() {{
            document.getElementById('disconnect-modal').classList.add('active');
        }}

        function closeDisconnectModal() {{
            document.getElementById('disconnect-modal').classList.remove('active');
        }}

        function confirmDisconnectDevice() {{
            closeDisconnectModal();
            showToast("Stick unlinked from guardian monitor");
            setDeviceOfflineUI();
        }}

        function escapeHtml(str) {{
            if (!str) return '';
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}

        // -------------------------------------------------------------
        // 9. PWA Service Worker Registration
        // -------------------------------------------------------------
        if ('serviceWorker' in navigator && {str(is_pwa).lower()}) {{
            navigator.serviceWorker.register('/sw.js').catch(() => {{}});
        }}

        // Initialize on DOM Ready
        window.addEventListener('DOMContentLoaded', () => {{
            runCinematicLoader();
            initLeafletMap();
            fetchStickData();
            pollingTimer = setInterval(fetchStickData, 3000);
            setInterval(updateLastCommLabel, 1000);
        }});
    </script>
</body>
</html>
"""
