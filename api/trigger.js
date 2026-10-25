const crypto = require('crypto');

module.exports = async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-cron-secret, x-force');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Security Rule 1: POST only (reject GET or other methods)
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: "Method Not Allowed. Only POST requests are permitted."
    });
  }

  // Security Rule 2: Constant-time secret comparison with timingSafeEqual on fixed SHA-256 digest
  const expectedSecret = process.env.CRON_SECRET;
  const providedSecret = req.headers['x-cron-secret'];

  if (!expectedSecret || !providedSecret) {
    return res.status(401).json({
      success: false,
      error: "Unauthorized: Missing CRON_SECRET in environment or x-cron-secret header in request."
    });
  }

  // Hashing both secrets to 32-byte digests prevents secret length disclosure and guarantees timingSafeEqual buffer match
  const hExpected = crypto.createHash('sha256').update(String(expectedSecret)).digest();
  const hProvided = crypto.createHash('sha256').update(String(providedSecret)).digest();

  if (!crypto.timingSafeEqual(hExpected, hProvided)) {
    return res.status(401).json({
      success: false,
      error: "Unauthorized: Invalid secret."
    });
  }

  // Security Rule 3: Server-side fine-grained PAT only (no token in query string)
  const GITHUB_TOKEN = process.env.GITHUB_TOKEN || process.env.GH_PAT;
  const REPO = "nareshkashyap91/market-mentor-ai";
  const WORKFLOW_ID = "master_pulse.yml";

  if (!GITHUB_TOKEN) {
    return res.status(500).json({
      success: false,
      error: "Missing GitHub Personal Access Token (GITHUB_TOKEN) in server environment.",
      instructions: "Generate a Fine-Grained Personal Access Token (PAT) with 'Actions: Write' permission limited to repository 'nareshkashyap91/market-mentor-ai' and configure GITHUB_TOKEN in Vercel Environment Variables."
    });
  }

  // IST Market & Post-Market Window Guard (UTC + 5:30)
  const nowUtc = new Date();
  const istOffsetMs = 5.5 * 60 * 60 * 1000;
  const nowIst = new Date(nowUtc.getTime() + istOffsetMs);
  const istDay = nowIst.getUTCDay(); // 0 = Sunday, 6 = Saturday
  const istHours = nowIst.getUTCHours();
  const istMinutes = nowIst.getUTCMinutes();
  const istDecimal = istHours + istMinutes / 60;

  const isWeekend = istDay === 0 || istDay === 6;
  // Active window: 8:45 AM (8.75) to 6:30 PM (18.5) IST covers live trading + 5:00 PM Momentum Wrap
  const isOffHours = istDecimal < 8.75 || istDecimal > 18.5;
  const isForced = req.headers['x-force'] === 'true' || req.headers['x-force'] === '1';

  if (!isForced && (isWeekend || isOffHours)) {
    return res.status(200).json({
      success: false,
      message: `Trigger skipped: Outside Indian Market & EOD Wrap Window (IST: ${nowIst.toISOString()}). No night or weekend runs.`,
      is_off_hours: true
    });
  }

  try {
    const ghRes = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW_ID}/dispatches`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${GITHUB_TOKEN}`,
          "Accept": "application/vnd.github.v3+json",
          "User-Agent": "MarketMentor-Vercel-Cron-Trigger"
        },
        body: JSON.stringify({ ref: "main" })
      }
    );

    if (ghRes.ok || ghRes.status === 204) {
      return res.status(200).json({
        success: true,
        message: "🚀 GitHub Actions Master Pulse Workflow Triggered Successfully in the Cloud!",
        timestamp: new Date().toISOString()
      });
    } else {
      const errText = await ghRes.text();
      return res.status(ghRes.status).json({
        success: false,
        error: `GitHub API returned ${ghRes.status}`,
        details: errText
      });
    }
  } catch (err) {
    return res.status(500).json({
      success: false,
      error: err.message
    });
  }
};
