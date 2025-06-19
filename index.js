import fetch from "node-fetch";

export default async function handler(req, res) {
  const API_URL = "https://api.casinoscores.com/svc-evolution-game-events/api/xxxtremelightningroulette/latest";
  try {
    const response = await fetch(API_URL, {
      headers: { "User-Agent": "Mozilla/5.0" }
    });
    const data = await response.json();
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.status(200).json(data);
  } catch (err) {
    res.status(500).json({ error: "Falha ao consultar API" });
  }
}
