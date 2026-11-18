// SGCI alert sign-up — Vercel serverless function (POST /api/contact).
// Forwards the visitor's e-mail address to the SGCI inbox through Resend (https://resend.com).
// Environment variables (Vercel > Project > Settings > Environment Variables):
//   RESEND_API_KEY  required. Without it the function answers {fallback:true}
//                   and the website opens the visitor's e-mail app instead, as before.
//   CONTACT_TO      optional, default contact@sgci-niger.com
//   CONTACT_FROM    optional, default "Site SGCI <site@sgci-niger.com>" (domain verified in Resend)

const hits = new Map(); // simple per-instance rate limit
function limited(ip) {
  const now = Date.now(), win = 10 * 60 * 1000, max = 5;
  const arr = (hits.get(ip) || []).filter((t) => now - t < win);
  arr.push(now); hits.set(ip, arr);
  return arr.length > max;
}
const one = (v, n) => String(v == null ? "" : v).replace(/[\r\n\t]+/g, " ").trim().slice(0, n);

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("content-type", "application/json; charset=utf-8");
  const end = (code, obj) => { res.statusCode = code; return res.end(JSON.stringify(obj)); };
  if (req.method !== "POST") return end(405, { error: "method" });
  const key = process.env.RESEND_API_KEY;
  if (!key) return end(503, { fallback: true });
  const ip = (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "x";
  if (limited(ip)) return end(429, { error: "rate" });

  let b = req.body;
  try { if (typeof b === "string") b = JSON.parse(b); } catch (e) { b = null; }
  if (!b || typeof b !== "object") return end(400, { error: "input" });
  if (one(b.website, 200)) return end(200, { ok: true }); // honeypot: filled only by bots
  const email = one(b.email, 200), lang = one(b.lang, 5);
  if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email)) return end(400, { error: "input" });

  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer " + key },
      body: JSON.stringify({
        from: process.env.CONTACT_FROM || "Site SGCI <site@sgci-niger.com>",
        to: [process.env.CONTACT_TO || "contact@sgci-niger.com"],
        reply_to: email,
        subject: "Inscription aux alertes opportunités SGCI",
        text: "Nouvelle inscription aux alertes (appels d'offre, AMI, opportunités).\n\nAdresse : " + email + "\nLangue du site : " + (lang || "fr"),
      }),
    });
    return r.ok ? end(200, { ok: true }) : end(502, { fallback: true });
  } catch (e) {
    return end(502, { fallback: true });
  }
};
