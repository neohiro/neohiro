"""Generate branded 1280x640 social preview banners."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:\Users\skele\Documents\GitHub Manager\social-previews"
os.makedirs(OUT, exist_ok=True)
W, H = 1280, 640
BG1, BG2 = (11, 14, 18), (22, 30, 38)

def font(name, size):
    for cand in (name, "segoeuib.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:\\Windows\\Fonts\\{cand}", size)
        except Exception:
            continue
    return ImageFont.load_default()

def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def rounded(draw, box, r, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def alien(draw, cx, cy, s, tint):
    """Simple alien-head motif: ellipse head + two large dark almond eyes."""
    head_w, head_h = int(3.4*s), int(4.2*s)
    box = [cx-head_w//2, cy-head_h//2, cx+head_w//2, cy+head_h//2]
    draw.ellipse(box, fill=tint)
    # antennae-ish top taper handled by eye shape contrast; keep minimal
    for dx in (-int(0.75*s), int(0.75*s)):
        ew, eh = int(1.15*s), int(1.9*s)
        ebox = [cx+dx-ew//2, cy-int(0.35*s)-eh//2,
                cx+dx+ew//2, cy-int(0.35*s)+eh//2]
        draw.ellipse(ebox, fill=(8, 10, 13))
        # slight tilt illusion: small highlight
        draw.ellipse([ebox[0]+3, ebox[1]+5, ebox[0]+9, ebox[1]+18],
                     fill=mix(tint, (255,255,255), 0.25))

def banner(repo, tagline, accent_hex, fname, kicker="OPEN SOURCE"):
    accent = tuple(int(accent_hex[i:i+2], 16) for i in (1, 3, 5))
    img = Image.new("RGB", (W, H), BG1)
    d = ImageDraw.Draw(img)
    # vertical gradient
    for y in range(H):
        d.line([(0, y), (W, y)], fill=mix(BG1, BG2, y / H))
    # faint grid
    grid = mix(BG2, accent, 0.08)
    for x in range(0, W, 64):
        d.line([(x, 0), (x, H)], fill=grid)
    for y in range(0, H, 64):
        d.line([(0, y), (W, y)], fill=grid)
    # accent glow bar bottom
    d.rectangle([0, H-10, W, H], fill=accent)

    f_kick = font("segoeuisl.ttf", 26) or font("segoeuil.ttf", 26)
    f_title = font("segoeuib.ttf", 84)
    f_tag = font("segoeuil.ttf", 36)
    f_url = font("segoeuib.ttf", 26)

    x0, y0 = 72, 96
    d.text((x0, y0), kicker.upper(), font=f_kick, fill=accent)
    tw = d.textlength(kicker.upper(), font=f_kick)
    d.rectangle([x0, y0+42, x0+max(tw, 90), y0+46], fill=accent)

    # title possibly two lines
    words = repo.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=f_title) > 900 and cur:
            lines.append(cur); cur = wd
        else:
            cur = trial
    lines.append(cur)
    ty = y0 + 78
    for ln in lines:
        d.text((x0, ty), ln, font=f_title, fill=(236, 239, 241))
        ty += 96
    d.text((x0, ty + 18), tagline, font=f_tag, fill=(150, 168, 180))
    d.text((x0, H-70), "github.com/neohiro", font=f_url, fill=(110, 130, 145))

    # alien motif right side, inside soft card
    card_x = W - 330
    rounded(d, [card_x, 120, W-60, 520], 40, fill=mix(BG2, (255,255,255), 0.04),
            outline=accent, width=3)
    rounded(d, [card_x+8, 128, W-68, 512], 34, outline=mix(accent, BG1, 0.55), width=1)
    alien(d, card_x + 135, 320, 62, mix(accent, (200, 210, 220), 0.45))

    path = os.path.join(OUT, fname)
    img.save(path, "PNG")
    print("wrote", fname)

banner("ExploitProtection", "Windows Exploit Protection Settings (Ultimate) GUI",
       "#66BB6A", "ExploitProtection.png")
banner("dnscrypt-proxy-gui", "Encrypted DNS, beautifully simple.",
       "#42A5F5", "dnscrypt-proxy-gui.png")
banner("Cripple-NetStrip", "See everything. Control everything. Trust nothing.",
       "#EF5350", "Cripple-NetStrip.png")
banner("BlackGlass", "Multi-client chat viewer for Second Life.",
       "#AB47BC", "BlackGlass.png")
banner("HoneyScan", "Passive honeypot for your home network.",
       "#FFA726", "HoneyScan.png")
banner("SystemMonitor", "Live system health, right on your desktop.",
       "#26C6DA", "SystemMonitor.png")
banner("neohiro", "Security hardening & privacy tools for Windows and Linux.",
       "#7E57C2", "profile.png", kicker="METAPOD")
print("done")
