"""
DRMYN Studio — Repository-Governed Workflow Diagram Generator v2
Visually rich version with icons, shadows, gradients for scientific publication.
Produces: workflow_diagram.svg + workflow_diagram.pdf
"""
import svgwrite
from svgwrite import mm
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(OUT_DIR, "workflow_diagram.svg")
HTML_PATH = os.path.join(OUT_DIR, "preview_diagram.html")

# ── SVG icon paths (simplified, hand-drawn style) ───────────
ICONS = {
    "book": "M3,1 L3,11 L9,11 L9,1 L3,1 M5,1 L5,11 M3,3 L5,3 M5,4 L9,4 M5,6 L9,6 M5,8 L9,8",
    "grid": "M1,1 L1,5 L5,5 L5,1 Z M7,1 L7,5 L11,5 L11,1 Z M1,7 L1,11 L5,11 L5,7 Z M7,7 L7,11 L11,11 L11,7 Z",
    "cycle": "M6,1 A5,5 0 1,1 1,6 M1,6 L1,3.5 M1,6 L3.5,6 M6,11 A5,5 0 1,1 11,6 M11,6 L11,8.5 M11,6 L8.5,6",
    "film": "M1,2 L11,2 L11,10 L1,10 Z M1,2 L1,10 M3,2 L3,10 M1,4 L3,4 M1,6 L3,6 M1,8 L3,8 M9,2 L9,10 M9,4 L11,4 M9,6 L11,6 M9,8 L11,8 M5,5 L5,7 L7,6 Z",
    "shield": "M6,1 L1,3 L1,7 C1,10 6,12 6,12 C6,12 11,10 11,7 L11,3 Z M4,6 L5.5,7.5 L8,4.5",
    "doc": "M3,1 L3,11 L9,11 L9,3 L7,1 Z M7,1 L7,3 L9,3 M5,5 L8,5 M5,7 L8,7 M5,9 L7,9",
    "location": "M6,1 C3,1 1,3.5 1,6 C1,9 6,12 6,12 C6,12 11,9 11,6 C11,3.5 9,1 6,1 Z M6,4 A2,2 0 1,1 6,8 A2,2 0 1,1 6,4",
    "eye": "M1,6 C3,2 9,2 11,6 C9,10 3,10 1,6 Z M6,4 A2,2 0 1,1 6,8 A2,2 0 1,1 6,4",
    "camera": "M1,3 L1,9 L11,9 L11,3 L8,3 L7,1.5 L5,1.5 L4,3 Z M6,4.5 A2,2 0 1,1 6,8.5 A2,2 0 1,1 6,4.5",
    "play": "M3,1 L3,11 L10,6 Z",
    "lock": "M3,5 L3,11 L9,11 L9,5 Z M4,5 L4,3 A2,2 0 1,1 8,3 L8,5 M6,7 L6,9",
    "check": "M2,6 L5,9 L10,3",
    "globe": "M6,1 A5,5 0 1,1 6,11 A5,5 0 1,1 6,1 M1,6 L11,6 M6,1 C4,3 4,9 6,11 M6,1 C8,3 8,9 6,11",
    "git": "M6,1 L6,11 M6,3 A2,2 0 1,1 10,3 M6,7 L3,7 A0,0 0 0,1 3,9",
    "star": "M6,1 L7.2,4.5 L11,4.5 L8,7 L9.2,11 L6,8.5 L2.8,11 L4,7 L1,4.5 L4.8,4.5 Z",
    "arrow_right": "M1,6 L9,6 M6,3 L9,6 L6,9",
    "layers": "M6,1 L1,4 L6,7 L11,4 Z M1,6.5 L6,9.5 L11,6.5 M1,9 L6,12 L11,9",
}


def make_svg():
    W, H = 200, 108
    dwg = svgwrite.Drawing(SVG_PATH, size=(f"{W}mm", f"{H}mm"),
                           viewBox=f"0 0 {W} {H}")

    dwg.defs.add(dwg.style("""
        text { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
    """))

    # ── Gradients ──
    for name, c1, c2 in [
        ("gSrc", "#43A047", "#2E7D32"),
        ("gPlan", "#1E88E5", "#1565C0"),
        ("gPrompt", "#FB8C00", "#E65100"),
        ("gSpine", "#8E24AA", "#6A1B9A"),
        ("gEvid", "#546E7A", "#37474F"),
        ("gGov", "#FAFAFA", "#EEEEEE"),
    ]:
        lg = dwg.linearGradient(id=name, x1="0%", y1="0%", x2="0%", y2="100%")
        lg.add_stop_color(0, c1)
        lg.add_stop_color(1, c2)
        dwg.defs.add(lg)

    # ── Drop shadow filter (raw XML) ──
    from svgwrite.etree import etree
    filt_el = etree.SubElement(dwg.defs.get_xml(), "filter",
        id="shadow", x="-5%", y="-5%", width="120%", height="130%")
    etree.SubElement(filt_el, "feGaussianBlur",
        attrib={"in": "SourceAlpha", "stdDeviation": "0.6", "result": "blur"})
    etree.SubElement(filt_el, "feOffset",
        attrib={"in": "blur", "dx": "0.3", "dy": "0.5", "result": "offsetBlur"})
    merge_el = etree.SubElement(filt_el, "feMerge")
    etree.SubElement(merge_el, "feMergeNode", attrib={"in": "offsetBlur"})
    etree.SubElement(merge_el, "feMergeNode", attrib={"in": "SourceGraphic"})

    # Glow filter for approval boundary
    glow_el = etree.SubElement(dwg.defs.get_xml(), "filter",
        id="glow", x="-10%", y="-10%", width="120%", height="120%")
    etree.SubElement(glow_el, "feGaussianBlur",
        attrib={"in": "SourceAlpha", "stdDeviation": "0.8", "result": "blur"})
    etree.SubElement(glow_el, "feFlood",
        attrib={"flood-color": "#C62828", "flood-opacity": "0.2", "result": "color"})
    etree.SubElement(glow_el, "feComposite",
        attrib={"in": "color", "in2": "blur", "operator": "in", "result": "shadow"})
    m2_el = etree.SubElement(glow_el, "feMerge")
    etree.SubElement(m2_el, "feMergeNode", attrib={"in": "shadow"})
    etree.SubElement(m2_el, "feMergeNode", attrib={"in": "SourceGraphic"})

    # ── Helpers ──
    def icon(x, y, path_d, color="#FFF", scale=1.0, sw=0.5):
        g = dwg.g(transform=f"translate({x},{y}) scale({scale*0.001*3.2})")
        g.add(dwg.path(d=path_d, fill="none", stroke=color,
                       stroke_width=sw/scale, stroke_linecap="round",
                       stroke_linejoin="round"))
        return g

    def icon_badge(cx, cy, icon_path, bg_color, icon_color="#FFF", r=3.5):
        g = dwg.g()
        g.add(dwg.circle(center=(cx, cy), r=r, fill=bg_color, opacity=0.15))
        g.add(dwg.circle(center=(cx, cy), r=r*0.75, fill=bg_color, opacity=0.9))
        ic = dwg.g(transform=f"translate({cx-r*0.4},{cy-r*0.4}) scale({r*0.065})")
        ic.add(dwg.path(d=icon_path, fill="none", stroke=icon_color,
                        stroke_width=1.2, stroke_linecap="round",
                        stroke_linejoin="round"))
        g.add(ic)
        return g

    def num_badge(cx, cy, num, color):
        g = dwg.g()
        g.add(dwg.circle(center=(cx, cy), r=3, fill=color,
                          filter="url(#shadow)"))
        g.add(dwg.text(str(num), insert=(cx, cy+0.8),
                        font_size="3", fill="#FFF", font_weight="700",
                        text_anchor="middle"))
        return g

    def card(x, y, w, h, grad_id, border_color):
        g = dwg.g(filter="url(#shadow)")
        g.add(dwg.rect(insert=(x, y), size=(w, h),
                        fill="#FFFFFF", stroke=border_color,
                        stroke_width=0.4, rx=2.5, ry=2.5))
        # Header gradient bar
        clip_id = f"hclip-{x}-{y}"
        clip = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip.add(dwg.rect(insert=(x, y), size=(w, h), rx=2.5, ry=2.5))
        hg = dwg.g(clip_path=f"url(#{clip_id})")
        hg.add(dwg.rect(insert=(x, y), size=(w, 10),
                          fill=f"url(#{grad_id})"))
        g.add(hg)
        return g

    def text(x, y, txt, size=2.2, color="#333", weight="normal", anchor="middle"):
        return dwg.text(txt, insert=(x, y),
                        font_size=str(size), fill=color,
                        font_weight=weight, text_anchor=anchor,
                        dominant_baseline="central")

    def sub_item(x, y, icon_path, label, color, icon_color=None):
        g = dwg.g()
        ic = dwg.g(transform=f"translate({x-1.2},{y-1.2}) scale(0.2)")
        ic.add(dwg.path(d=icon_path, fill="none",
                        stroke=icon_color or color,
                        stroke_width=1.5, stroke_linecap="round",
                        stroke_linejoin="round"))
        g.add(ic)
        g.add(text(x+2, y, label, size=1.9, color="#555", anchor="start"))
        return g

    def curved_arrow(x1, y1, x2, y2, color="#444", sw=0.5):
        g = dwg.g()
        mx = (x1 + x2) / 2
        g.add(dwg.path(
            d=f"M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}",
            fill="none", stroke=color, stroke_width=sw,
            stroke_linecap="round"
        ))
        # arrowhead
        g.add(dwg.polygon(
            points=[(x2-1, y2-0.6), (x2+0.2, y2), (x2-1, y2+0.6)],
            fill=color
        ))
        return g

    def straight_arrow(x1, y1, x2, y2, color="#444", sw=0.5):
        g = dwg.g()
        g.add(dwg.line(start=(x1, y1), end=(x2-0.8, y2),
                        stroke=color, stroke_width=sw))
        g.add(dwg.polygon(
            points=[(x2-1.5, y2-0.6), (x2, y2), (x2-1.5, y2+0.6)],
            fill=color
        ))
        return g

    # ── Background subtle pattern ──
    dwg.add(dwg.rect(insert=(0, 0), size=(W, H), fill="#FAFBFC"))

    # ── Layout ──
    BOX_W = 30
    BOX_H = 52
    SPINE_W = 38
    SPINE_H = 58
    SEP = 7
    Y_TOP = 16

    X1 = 6
    X2 = X1 + BOX_W + SEP
    X3 = X2 + BOX_W + SEP
    X4 = X3 + BOX_W + SEP
    X5 = X4 + SPINE_W + SEP

    # ═══════════════════════════════════════════════════════════
    #  HUMAN APPROVAL GATE (background layer)
    # ═══════════════════════════════════════════════════════════
    hb_x = X2 - 3
    hb_y = Y_TOP - 7
    hb_w = (X4 + SPINE_W) - X2 + 6
    hb_h = SPINE_H + 16
    dwg.add(dwg.rect(insert=(hb_x, hb_y), size=(hb_w, hb_h),
                      fill="#C62828", fill_opacity=0.03,
                      stroke="#C62828", stroke_width=0.7,
                      stroke_dasharray="2.5,1.5",
                      rx=4, ry=4, filter="url(#glow)"))
    # Gate label with icon
    gate_g = dwg.g()
    gate_g.add(dwg.rect(insert=(hb_x + hb_w/2 - 14, hb_y - 2.5),
                          size=(28, 5), fill="#C62828", rx=2.5, ry=2.5,
                          filter="url(#shadow)"))
    gate_ic = dwg.g(transform=f"translate({hb_x + hb_w/2 - 12},{hb_y - 1.8}) scale(0.25)")
    gate_ic.add(dwg.path(d=ICONS["lock"], fill="none", stroke="#FFF",
                          stroke_width=1.3, stroke_linecap="round",
                          stroke_linejoin="round"))
    gate_g.add(gate_ic)
    gate_g.add(text(hb_x + hb_w/2 + 1, hb_y, "Human Approval Gate",
                     size=2.5, color="#FFF", weight="700"))
    dwg.add(gate_g)

    # ═══════════════════════════════════════════════════════════
    #  BOX 1 — SOURCE TRUTH
    # ═══════════════════════════════════════════════════════════
    b1 = card(X1, Y_TOP, BOX_W, BOX_H, "gSrc", "#2E7D32")
    b1.add(icon_badge(X1 + BOX_W/2, Y_TOP + 5, ICONS["book"], "#FFF"))
    b1.add(text(X1 + BOX_W/2, Y_TOP + 12.5, "Source Truth",
                 size=2.8, color="#FFF", weight="700"))
    dwg.add(b1)
    dwg.add(num_badge(X1 + 3, Y_TOP - 2, "1", "#2E7D32"))

    items1 = [
        (ICONS["doc"], "Screenplay"),
        (ICONS["doc"], "Story Blueprint"),
        (ICONS["doc"], "Character Dossier"),
        (ICONS["doc"], "Continuity & Style Bibles"),
        (ICONS["doc"], "Project Config"),
    ]
    for i, (ic, lbl) in enumerate(items1):
        dwg.add(sub_item(X1 + 3, Y_TOP + 17 + i*4.5, ic, lbl, "#2E7D32"))

    # ═══════════════════════════════════════════════════════════
    #  BOX 2 — STRUCTURED PLANNING
    # ═══════════════════════════════════════════════════════════
    b2 = card(X2, Y_TOP, BOX_W, BOX_H, "gPlan", "#1565C0")
    b2.add(icon_badge(X2 + BOX_W/2, Y_TOP + 5, ICONS["grid"], "#FFF"))
    b2.add(text(X2 + BOX_W/2, Y_TOP + 12.5, "Structured Planning",
                 size=2.6, color="#FFF", weight="700"))
    dwg.add(b2)
    dwg.add(num_badge(X2 + 3, Y_TOP - 2, "2", "#1565C0"))

    items2 = [
        (ICONS["layers"], "Scene Cards (120)"),
        (ICONS["star"], "Element Records"),
        (ICONS["git"], "Continuity Graph"),
        (ICONS["eye"], "Aesthetic Bible"),
    ]
    for i, (ic, lbl) in enumerate(items2):
        dwg.add(sub_item(X2 + 3, Y_TOP + 17 + i*4.5, ic, lbl, "#1565C0"))

    # ═══════════════════════════════════════════════════════════
    #  BOX 3 — PROMPT LIFECYCLE
    # ═══════════════════════════════════════════════════════════
    b3 = card(X3, Y_TOP, BOX_W, BOX_H, "gPrompt", "#E65100")
    b3.add(icon_badge(X3 + BOX_W/2, Y_TOP + 5, ICONS["cycle"], "#FFF"))
    b3.add(text(X3 + BOX_W/2, Y_TOP + 12.5, "Prompt Lifecycle",
                 size=2.6, color="#FFF", weight="700"))
    dwg.add(b3)
    dwg.add(num_badge(X3 + 3, Y_TOP - 2, "3", "#E65100"))

    # Lifecycle pipeline with connected nodes
    states = [
        ("draft", "#FFF3E0", "#E65100"),
        ("review", "#FFF3E0", "#F57C00"),
        ("approved", "#FFF3E0", "#EF6C00"),
        ("locked", "#E65100", "#FFFFFF"),
    ]
    pipeline_x = X3 + BOX_W/2
    for i, (label, bg, fg) in enumerate(states):
        sy = Y_TOP + 18 + i * 7.5
        # Connector line
        if i > 0:
            dwg.add(dwg.line(start=(pipeline_x, sy - 4.2),
                              end=(pipeline_x, sy - 1.5),
                              stroke="#E65100", stroke_width=0.4,
                              stroke_opacity=0.5))
            dwg.add(dwg.polygon(
                points=[(pipeline_x - 0.5, sy - 2),
                         (pipeline_x, sy - 1),
                         (pipeline_x + 0.5, sy - 2)],
                fill="#E65100", opacity=0.6
            ))
        # State pill
        pill_w = 18
        pill_h = 4.2
        dwg.add(dwg.rect(insert=(pipeline_x - pill_w/2, sy - pill_h/2),
                           size=(pill_w, pill_h),
                           fill=bg, stroke="#E65100", stroke_width=0.35,
                           rx=pill_h/2, ry=pill_h/2))
        dwg.add(text(pipeline_x, sy, label, size=2, color=fg, weight="600"))

    # ═══════════════════════════════════════════════════════════
    #  BOX 4 — PRODUCTION SPINE
    # ═══════════════════════════════════════════════════════════
    b4 = card(X4, Y_TOP, SPINE_W, SPINE_H, "gSpine", "#6A1B9A")
    b4.add(icon_badge(X4 + SPINE_W/2, Y_TOP + 5, ICONS["film"], "#FFF"))
    b4.add(text(X4 + SPINE_W/2, Y_TOP + 12.5, "Production Spine",
                 size=2.8, color="#FFF", weight="700"))
    dwg.add(b4)
    dwg.add(num_badge(X4 + 3, Y_TOP - 2, "4", "#6A1B9A"))

    bands = [
        ("A", "#8E24AA", ICONS["eye"], "Element Identity", "Reference Packs, QC,", "Element Bindings"),
        ("B", "#7B1FA2", ICONS["camera"], "Previsualization", "Scene Stills,", "Shot Manifests"),
        ("C", "#6A1B9A", ICONS["play"], "Clip Selection", "Video Takes,", "Scene Clip Map"),
    ]
    band_x = X4 + 2
    band_w = SPINE_W - 4
    for i, (letter, color, ic_path, title, sub1, sub2) in enumerate(bands):
        by = Y_TOP + 17 + i * 13.5
        # Band card
        dwg.add(dwg.rect(insert=(band_x, by), size=(band_w, 12),
                           fill="#F3E5F5", stroke="#6A1B9A",
                           stroke_width=0.25, rx=2, ry=2))
        # Letter badge
        dwg.add(dwg.circle(center=(band_x + 3, by + 4), r=2.2,
                             fill=color))
        dwg.add(text(band_x + 3, by + 4.2, letter,
                      size=2.2, color="#FFF", weight="700"))
        # Icon
        ic_g = dwg.g(transform=f"translate({band_x + 6.5},{by + 2}) scale(0.22)")
        ic_g.add(dwg.path(d=ic_path, fill="none", stroke=color,
                           stroke_width=1.2, stroke_linecap="round",
                           stroke_linejoin="round"))
        dwg.add(ic_g)
        # Title
        dwg.add(text(band_x + 11, by + 3.5, title,
                      size=2, color="#6A1B9A", weight="600", anchor="start"))
        # Subtitles
        dwg.add(text(band_x + 11, by + 6.5, sub1,
                      size=1.7, color="#777", anchor="start"))
        dwg.add(text(band_x + 11, by + 9, sub2,
                      size=1.7, color="#777", anchor="start"))
        # Connector between bands
        if i < len(bands) - 1:
            cy = by + 12
            dwg.add(dwg.line(start=(band_x + band_w/2, cy + 0.2),
                              end=(band_x + band_w/2, cy + 1.2),
                              stroke="#6A1B9A", stroke_width=0.3,
                              stroke_opacity=0.4))

    # ═══════════════════════════════════════════════════════════
    #  BOX 5 — EVIDENCE & RELEASE
    # ═══════════════════════════════════════════════════════════
    b5 = card(X5, Y_TOP, BOX_W, BOX_H, "gEvid", "#37474F")
    b5.add(icon_badge(X5 + BOX_W/2, Y_TOP + 5, ICONS["shield"], "#FFF"))
    b5.add(text(X5 + BOX_W/2, Y_TOP + 12.5, "Evidence & Release",
                 size=2.5, color="#FFF", weight="700"))
    dwg.add(b5)
    dwg.add(num_badge(X5 + 3, Y_TOP - 2, "5", "#37474F"))

    items5 = [
        (ICONS["check"], "Schema Validation"),
        (ICONS["lock"], "Canon Freeze"),
        (ICONS["layers"], "Reproducible Audit Trail"),
    ]
    for i, (ic, lbl) in enumerate(items5):
        dwg.add(sub_item(X5 + 3, Y_TOP + 17 + i*4.5, ic, lbl, "#37474F"))

    # Release endpoints with icons
    ep_y = Y_TOP + 35
    # Private
    dwg.add(dwg.rect(insert=(X5 + 2, ep_y), size=(12, 8),
                       fill="#ECEFF1", stroke="#546E7A",
                       stroke_width=0.3, rx=2, ry=2))
    git_ic = dwg.g(transform=f"translate({X5+5.5},{ep_y+1.5}) scale(0.18)")
    git_ic.add(dwg.path(d=ICONS["git"], fill="none", stroke="#37474F",
                         stroke_width=1.3, stroke_linecap="round",
                         stroke_linejoin="round"))
    dwg.add(git_ic)
    dwg.add(text(X5 + 8, ep_y + 6, "Private", size=1.6, color="#37474F", weight="600"))
    dwg.add(text(X5 + 8, ep_y + 7.8, "(GitHub)", size=1.3, color="#777"))

    # Public
    dwg.add(dwg.rect(insert=(X5 + 16, ep_y), size=(12, 8),
                       fill="#ECEFF1", stroke="#546E7A",
                       stroke_width=0.3, rx=2, ry=2))
    globe_ic = dwg.g(transform=f"translate({X5+19.5},{ep_y+1.5}) scale(0.18)")
    globe_ic.add(dwg.path(d=ICONS["globe"], fill="none", stroke="#37474F",
                           stroke_width=1.3, stroke_linecap="round",
                           stroke_linejoin="round"))
    dwg.add(globe_ic)
    dwg.add(text(X5 + 22, ep_y + 6, "Public", size=1.6, color="#37474F", weight="600"))
    dwg.add(text(X5 + 22, ep_y + 7.8, "(DOI)", size=1.3, color="#777"))

    # Fork lines
    mid_x = X5 + BOX_W / 2
    dwg.add(dwg.line(start=(mid_x, ep_y - 3), end=(mid_x, ep_y - 1.5),
                      stroke="#546E7A", stroke_width=0.4))
    dwg.add(dwg.line(start=(X5 + 8, ep_y - 1.5), end=(X5 + 22, ep_y - 1.5),
                      stroke="#546E7A", stroke_width=0.4))
    dwg.add(dwg.line(start=(X5 + 8, ep_y - 1.5), end=(X5 + 8, ep_y),
                      stroke="#546E7A", stroke_width=0.4))
    dwg.add(dwg.line(start=(X5 + 22, ep_y - 1.5), end=(X5 + 22, ep_y),
                      stroke="#546E7A", stroke_width=0.4))

    # ═══════════════════════════════════════════════════════════
    #  MAIN FLOW ARROWS (curved)
    # ═══════════════════════════════════════════════════════════
    arrow_y = Y_TOP + BOX_H / 2
    for ax1, ax2 in [(X1+BOX_W, X2), (X2+BOX_W, X3),
                      (X3+BOX_W, X4), (X4+SPINE_W, X5)]:
        dwg.add(straight_arrow(ax1 + 0.5, arrow_y, ax2 - 0.5, arrow_y,
                                color="#555", sw=0.6))

    # ═══════════════════════════════════════════════════════════
    #  REVISION LOOP
    # ═══════════════════════════════════════════════════════════
    loop_y = Y_TOP + SPINE_H + 4
    loop_sx = X4 + SPINE_W / 2
    loop_ex = X2 + BOX_W / 2
    path_d = (f"M{loop_sx},{Y_TOP + SPINE_H} "
              f"L{loop_sx},{loop_y} "
              f"L{loop_ex},{loop_y} "
              f"L{loop_ex},{Y_TOP + BOX_H + 1}")
    dwg.add(dwg.path(d=path_d, fill="none", stroke="#999",
                      stroke_width=0.4, stroke_dasharray="2,1.2",
                      stroke_linecap="round"))
    dwg.add(dwg.polygon(
        points=[(loop_ex - 0.5, Y_TOP + BOX_H + 1.5),
                 (loop_ex, Y_TOP + BOX_H),
                 (loop_ex + 0.5, Y_TOP + BOX_H + 1.5)],
        fill="#999"
    ))
    # Label with background
    lbl_x = (loop_sx + loop_ex) / 2
    lbl_y = loop_y
    dwg.add(dwg.rect(insert=(lbl_x - 7, lbl_y - 1.8), size=(14, 3.2),
                       fill="#FAFBFC", stroke="none", rx=1.5, ry=1.5))
    cycle_ic = dwg.g(transform=f"translate({lbl_x - 6},{lbl_y - 1.2}) scale(0.17)")
    cycle_ic.add(dwg.path(d=ICONS["cycle"], fill="none", stroke="#999",
                           stroke_width=1.2, stroke_linecap="round",
                           stroke_linejoin="round"))
    dwg.add(cycle_ic)
    dwg.add(text(lbl_x + 1, lbl_y, "revision loop",
                  size=1.8, color="#999", weight="normal"))

    # ═══════════════════════════════════════════════════════════
    #  GOVERNANCE BAR
    # ═══════════════════════════════════════════════════════════
    gov_y = 92
    gov_h = 12
    gov_x = 4
    gov_w = W - 8

    dwg.add(dwg.rect(insert=(gov_x, gov_y), size=(gov_w, gov_h),
                       fill="url(#gGov)", stroke="#BDBDBD",
                       stroke_width=0.35, rx=3, ry=3,
                       filter="url(#shadow)"))

    dwg.add(text(gov_x + gov_w/2, gov_y + 3.5, "Governance Principles",
                  size=2.5, color="#333", weight="700"))

    principles = [
        (ICONS["doc"], "Source-Grounded"),
        (ICONS["check"], "Schema-Validated"),
        (ICONS["lock"], "Human-Approved"),
        (ICONS["star"], "Element-First"),
        (ICONS["shield"], "Reproducible Audit"),
    ]
    total_w = len(principles) * 28
    start_x = gov_x + gov_w/2 - total_w/2 + 5
    for i, (ic_path, label) in enumerate(principles):
        px = start_x + i * 32
        py = gov_y + 8.5
        # Small icon
        pic = dwg.g(transform=f"translate({px-2},{py-1.2}) scale(0.17)")
        pic.add(dwg.path(d=ic_path, fill="none", stroke="#666",
                          stroke_width=1.3, stroke_linecap="round",
                          stroke_linejoin="round"))
        dwg.add(pic)
        dwg.add(text(px + 1.5, py, label, size=1.8, color="#555", anchor="start"))
        # Separator dot
        if i < len(principles) - 1:
            dwg.add(dwg.circle(center=(px + 26, py), r=0.4, fill="#BDBDBD"))

    # ═══════════════════════════════════════════════════════════
    #  FIGURE LABEL
    # ═══════════════════════════════════════════════════════════
    dwg.add(text(W/2, 5, "DRMYN Studio: Repository-Governed Workflow for AI-Assisted Film Production",
                  size=3.5, color="#222", weight="700"))
    dwg.add(text(W/2, 8.5,
                  "A metadata-first architecture linking source truth, structured planning, and reproducible evidence",
                  size=2, color="#777"))

    dwg.save()
    print(f"SVG saved: {SVG_PATH}")

    # ── Also write HTML preview ──
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        svg_content = f.read()
    # Strip XML declaration for inline embedding
    svg_content = svg_content.replace('<?xml version="1.0" encoding="utf-8" ?>\n', '')

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>DRMYN Workflow Diagram</title>
<style>
body {{ margin: 30px; background: #f0f0f0; display: flex; flex-direction: column;
       align-items: center; font-family: sans-serif; }}
.container {{ background: white; padding: 20px; border-radius: 8px;
             box-shadow: 0 2px 12px rgba(0,0,0,0.1); max-width: 1100px; }}
svg {{ width: 100%; height: auto; }}
h3 {{ color: #555; margin-bottom: 5px; }}
</style></head><body>
<h3>Preview — workflow_diagram.svg</h3>
<div class="container">
{svg_content}
</div>
</body></html>"""
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML preview saved: {HTML_PATH}")


# ── PDF Generation ───────────────────────────────────────────
def make_pdf():
    from reportlab.graphics import renderPDF
    from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon, Group
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm as rl_mm

    W = 200
    H = 108
    d = Drawing(W * rl_mm, H * rl_mm)

    def ry(y):
        return (H - y) * rl_mm

    def rx(x):
        return x * rl_mm

    def add_rect(x, y, w, h, fill, stroke=None, sw=0.3):
        r = Rect(rx(x), ry(y+h), rx(w), h*rl_mm,
                 fillColor=HexColor(fill) if fill else None,
                 strokeColor=HexColor(stroke) if stroke else None,
                 strokeWidth=sw, rx=2.5*rl_mm, ry=2.5*rl_mm)
        d.add(r)

    def add_text(x, y, txt, size=2.2, color="#333", weight="normal", anchor="middle"):
        fn = "Helvetica-Bold" if weight in ("600","700","bold") else "Helvetica"
        s = String(rx(x), ry(y) - size*0.35, txt,
                   fontSize=size, fillColor=HexColor(color),
                   fontName=fn, textAnchor=anchor)
        d.add(s)

    def add_circle(cx, cy, r, fill):
        c = Circle(rx(cx), ry(cy), r*rl_mm,
                   fillColor=HexColor(fill), strokeColor=None)
        d.add(c)

    def add_line(x1, y1, x2, y2, color="#333", sw=0.4, dashed=False):
        ln = Line(rx(x1), ry(y1), rx(x2), ry(y2),
                  strokeColor=HexColor(color), strokeWidth=sw)
        if dashed:
            ln.strokeDashArray = [2*rl_mm, 1.2*rl_mm]
        d.add(ln)

    # Background
    add_rect(0, 0, W, H, "#FAFBFC", None, 0)

    # Title
    add_text(W/2, 5, "DRMYN Studio: Repository-Governed Workflow for AI-Assisted Film Production",
             size=3.5, color="#222", weight="700")
    add_text(W/2, 8.5,
             "A metadata-first architecture linking source truth, structured planning, and reproducible evidence",
             size=2, color="#777")

    BOX_W = 30; BOX_H = 52; SPINE_W = 38; SPINE_H = 58; SEP = 7; Y_TOP = 16
    X1 = 6; X2 = X1+BOX_W+SEP; X3 = X2+BOX_W+SEP; X4 = X3+BOX_W+SEP; X5 = X4+SPINE_W+SEP

    # Human Approval Gate
    hb_x = X2 - 3; hb_y = Y_TOP - 7
    hb_w = (X4 + SPINE_W) - X2 + 6; hb_h = SPINE_H + 16
    r = Rect(rx(hb_x), ry(hb_y+hb_h), rx(hb_w), hb_h*rl_mm,
             fillColor=HexColor("#C6282808"),
             strokeColor=HexColor("#C62828"), strokeWidth=0.7,
             rx=4*rl_mm, ry=4*rl_mm,
             strokeDashArray=[2.5*rl_mm, 1.5*rl_mm])
    d.add(r)
    # Gate label bg
    add_rect(hb_x + hb_w/2 - 14, hb_y - 2.5, 28, 5, "#C62828", "#C62828", 0)
    add_text(hb_x + hb_w/2 + 1, hb_y, "Human Approval Gate",
             size=2.5, color="#FFFFFF", weight="700")

    # Boxes
    boxes = [
        (X1, Y_TOP, BOX_W, BOX_H, "#43A047", "#2E7D32", "1", "Source Truth",
         ["Screenplay", "Story Blueprint", "Character Dossier", "Continuity & Style Bibles", "Project Config"]),
        (X2, Y_TOP, BOX_W, BOX_H, "#1E88E5", "#1565C0", "2", "Structured Planning",
         ["Scene Cards (120)", "Element Records", "Continuity Graph", "Aesthetic Bible"]),
        (X3, Y_TOP, BOX_W, BOX_H, "#FB8C00", "#E65100", "3", "Prompt Lifecycle", []),
        (X5, Y_TOP, BOX_W, BOX_H, "#546E7A", "#37474F", "5", "Evidence & Release",
         ["Schema Validation", "Canon Freeze", "Reproducible Audit Trail"]),
    ]

    for bx, by, bw, bh, grad1, grad2, num, title, items in boxes:
        add_rect(bx, by, bw, bh, "#FFFFFF", grad2, 0.4)
        add_rect(bx, by, bw, 10, grad2, grad2, 0)
        add_text(bx + bw/2, by + 6, title, size=2.6, color="#FFFFFF", weight="700")
        add_circle(bx + 3, by - 2, 3, grad2)
        add_text(bx + 3, by - 2, num, size=3, color="#FFFFFF", weight="700")
        for i, item in enumerate(items):
            add_text(bx + bw/2, by + 15 + i*4.5, item, size=1.9, color="#555")

    # Box 3 states
    states = ["draft", "review", "approved", "locked"]
    for i, st in enumerate(states):
        sy = Y_TOP + 16 + i * 7.5
        add_rect(X3 + 6, sy, 18, 4.2, "#FFF3E0", "#E65100", 0.3)
        col = "#FFFFFF" if st == "locked" else "#E65100"
        if st == "locked":
            add_rect(X3 + 6, sy, 18, 4.2, "#E65100", "#E65100", 0.3)
        add_text(X3 + BOX_W/2, sy + 2.1, st, size=2, color=col, weight="600")

    # Box 4
    add_rect(X4, Y_TOP, SPINE_W, SPINE_H, "#FFFFFF", "#6A1B9A", 0.4)
    add_rect(X4, Y_TOP, SPINE_W, 10, "#6A1B9A", "#6A1B9A", 0)
    add_text(X4 + SPINE_W/2, Y_TOP + 6, "Production Spine",
             size=2.8, color="#FFFFFF", weight="700")
    add_circle(X4 + 3, Y_TOP - 2, 3, "#6A1B9A")
    add_text(X4 + 3, Y_TOP - 2, "4", size=3, color="#FFFFFF", weight="700")

    band_data = [
        ("A", "#8E24AA", "Element Identity", "Reference Packs, QC, Bindings"),
        ("B", "#7B1FA2", "Previsualization", "Scene Stills, Shot Manifests"),
        ("C", "#6A1B9A", "Clip Selection", "Video Takes, Scene Clip Map"),
    ]
    for i, (letter, color, title, sub) in enumerate(band_data):
        by = Y_TOP + 17 + i * 13.5
        add_rect(X4 + 2, by, SPINE_W - 4, 12, "#F3E5F5", "#6A1B9A", 0.25)
        add_circle(X4 + 5, by + 4, 2.2, color)
        add_text(X4 + 5, by + 4, letter, size=2.2, color="#FFFFFF", weight="700")
        add_text(X4 + SPINE_W/2 + 2, by + 3.5, title, size=2, color="#6A1B9A", weight="600")
        add_text(X4 + SPINE_W/2 + 2, by + 7, sub, size=1.7, color="#777")

    # Main arrows
    ay = Y_TOP + BOX_H / 2
    for ax1, ax2 in [(X1+BOX_W, X2), (X2+BOX_W, X3),
                      (X3+BOX_W, X4), (X4+SPINE_W, X5)]:
        add_line(ax1+0.5, ay, ax2-0.5, ay, "#555", 0.6)

    # Revision loop
    loop_y = Y_TOP + SPINE_H + 4
    add_line(X4+SPINE_W/2, Y_TOP+SPINE_H, X4+SPINE_W/2, loop_y, "#999", 0.4, True)
    add_line(X4+SPINE_W/2, loop_y, X2+BOX_W/2, loop_y, "#999", 0.4, True)
    add_line(X2+BOX_W/2, loop_y, X2+BOX_W/2, Y_TOP+BOX_H+1, "#999", 0.4, True)
    add_text((X4+SPINE_W/2 + X2+BOX_W/2)/2, loop_y - 1.2,
             "revision loop", size=1.8, color="#999")

    # Release endpoints
    ep_y = Y_TOP + 35
    add_rect(X5 + 2, ep_y, 12, 8, "#ECEFF1", "#546E7A", 0.3)
    add_text(X5 + 8, ep_y + 3.5, "Private (GitHub)", size=1.6, color="#37474F", weight="600")
    add_rect(X5 + 16, ep_y, 12, 8, "#ECEFF1", "#546E7A", 0.3)
    add_text(X5 + 22, ep_y + 3.5, "Public (DOI)", size=1.6, color="#37474F", weight="600")

    # Governance bar
    gov_y = 92; gov_h = 12; gov_x = 4; gov_w = W - 8
    add_rect(gov_x, gov_y, gov_w, gov_h, "#F5F5F5", "#BDBDBD", 0.35)
    add_text(gov_x + gov_w/2, gov_y + 3.5, "Governance Principles",
             size=2.5, color="#333", weight="700")
    add_text(gov_x + gov_w/2, gov_y + 8.5,
             "Source-Grounded  |  Schema-Validated  |  Human-Approved  |  Element-First  |  Reproducible Audit",
             size=1.8, color="#555")

    renderPDF.drawToFile(d, os.path.join(OUT_DIR, "workflow_diagram.pdf"), fmt="PDF")
    print(f"PDF saved: {os.path.join(OUT_DIR, 'workflow_diagram.pdf')}")


if __name__ == "__main__":
    make_svg()
    make_pdf()
