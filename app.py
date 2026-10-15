#... garde get_conn() et init_db() de V10.6 pareil...

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    if not rows: return "Pas de tirage"
    all_nums=[]
    th_list=[]; tb_list=[]
    for r in rows:
        for x in (r[4]+"-"+(r[5] or "")).split("-"):
            if x.strip().isdigit(): all_nums.append(x.strip())
        if r[8]: th_list.append(r[8])
        if r[9]: tb_list.append(r[9])

    cnt=Counter(all_nums)
    total=len(all_nums)
    top=sorted(cnt.items(), key=lambda x:x[1], reverse=True)[:15]
    top_data=[(n,c,round(c/total*100,1)) for n,c in top]
    bottom=sorted(cnt.items(), key=lambda x:x[1])[:5]

    # === NOUVEAU: STATS TOTAUX ===
    avg_h = int(sum(th_list)/len(th_list)) if th_list else 0
    avg_b = int(sum(tb_list)/len(tb_list)) if tb_list else 0
    min_h = min(th_list) if th_list else 0
    max_h = max(th_list) if th_list else 0
    min_b = min(tb_list) if tb_list else 0
    max_b = max(tb_list) if tb_list else 0

    from collections import defaultdict
    jeux=defaultdict(list)
    for r in rows: jeux[r[3]].append(r)

    pred_html=""
    for jeu_name, lst in jeux.items():
        nums=[]
        th=[]; tb=[]
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit(): nums.append(x.strip())
            if r[8]: th.append(r[8])
            if r[9]: tb.append(r[9])
        c=Counter(nums)
        chauds=c.most_common(3)
        retards=sorted(c.items(), key=lambda x:x[1])[:3]
        avg_th = int(sum(th)/len(th)) if th else 0
        avg_tb = int(sum(tb)/len(tb)) if tb else 0

        pred_html+=f"<div class='box'><h3 style='color:gold'>{jeu_name} - {len(lst)} tirages | TOTAL MOY: H:{avg_th} B:{avg_tb}</h3>"
        pred_html+=f"<p><span style='color:#00ff88'>Chauds:</span> "
        for n,cc in chauds:
            p=round(cc/len(nums)*100,1) if nums else 0
            pred_html+=f"<span class='badge hot'>{n} {p}%</span> "
        pred_html+=f"</p><p><span style='color:#ff4444'>Retard:</span> "
        for n,cc in retards:
            pred_html+=f"<span class='badge' style='background:#331111;color:#ff8888;border-color:red'>{n}</span> "
        pred_html+="</p></div>"

    chauds_msg=" ".join([n for n,c,p in top_data[:5]])
    retards_msg=" ".join([n for n,c in bottom])

    whatsapp_text=f"""🎯 LOTO TOGO V10.7 - PRONO DU JOUR

📊 TOTAL ANALYSIS:
WIN MOY: {avg_h} (Min:{min_h} Max:{max_h})
MACHINE MOY: {avg_b} (Min:{min_b} Max:{max_b})
➡️ Prochain TOTAL estimé: {avg_h}-{avg_h+15}

🔥 A TENTER (retard): {retards_msg}
⚠️ Chauds du moment: {chauds_msg}

💡 Prono 2 Sûr: {top_data[0][0] if top_data else ''} - {bottom[0][0] if bottom else ''}

👉 VIP 500F/jour - 2000F/semaine
📲 Inbox pour le 2 sûr

#LONATO #LotoTogo"""

    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
    body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}
  .top{{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}}
  .box{{background:#151515;padding:14px;margin:12px 0;border-radius:15px;border:1px solid #333}}
  .badge{{display:inline-block;background:#222;border:1px solid gold;color:gold;padding:7px 12px;border-radius:20px;margin:4px;font-weight:bold}}
  .hot{{background:gold;color:#111}}
  .total-box{{background:#1a2a1a;border:2px solid #00ff88}}
  .what{{background:#0a1a0a;border:2px solid gold;border-radius:15px;padding:15px}}
    pre{{background:#111;color:#0f0;padding:12px;border-radius:10px;white-space:pre-wrap;font-size:13px}}
    a{{color:gold}}
    </style></head><body>
    <div class="top"><h2>📊 V10.7 ANALYSE + 2 TOTAUX</h2><p>{len(rows)} tirages</p></div>
    <p><a href="/">← Accueil</a></p>

    <div class="box total-box"><h3>💰 TOTAL WIN / MACHINE - STATS PRO</h3>
    <p>🔝 <b>WIN (Haut):</b> Moy={avg_h} | Min={min_h} | Max={max_h}</p>
    <p>🔽 <b>MACHINE (Bas):</b> Moy={avg_b} | Min={min_b} | Max={max_b}</p>
    <p style="color:#00ff88">Si moyenne WIN > 250, prochain sera BAS. Si < 200, prochain sera HAUT.</p>
    </div>

    <div class="box"><h3>🔥 TOP 15 GLOBAL</h3>
    """ + "".join([f"<span class='badge hot'>{n} {p}% ({c}x)</span>" for n,c,p in top_data]) + f"""
    </div>
    {pred_html}
    <div class="what"><h3>💰 MESSAGE WHATSAPP VIP AVEC TOTAUX</h3>
    <pre id="msg">{whatsapp_text}</pre>
    <button onclick="navigator.clipboard.writeText(document.getElementById('msg').innerText);alert('Copié!')" style="background:gold;color:#111;padding:14px;width:100%;border:none;border-radius:12px;font-weight:bold">📋 COPIER LE MESSAGE</button>
    </div>
    </body></html>
    """)
