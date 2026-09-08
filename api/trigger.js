module.exports = async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN || process.env.GH_PAT;
  const REPO = "nareshkashyap91/market-mentor-ai";
  const WORKFLOW_ID = "master_pulse.yml";

  // If token is set in environment or provided via query param ?token=xxx
  const tokenToUse = (req.query && req.query.token) || GITHUB_TOKEN;

  if (!tokenToUse) {
    return res.status(400).json({
      success: false,
      error: "Missing GitHub Personal Access Token (GITHUB_TOKEN). Please add GITHUB_TOKEN in Vercel Environment Variables or pass ?token=YOUR_PAT",
      instructions: "Generate a Personal Access Token with 'Actions: Write' permission at https://github.com/settings/tokens"
    });
  }

  try {
    const ghRes = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW_ID}/dispatches`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${tokenToUse}`,
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
