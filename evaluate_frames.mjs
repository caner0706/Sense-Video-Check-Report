/**
 * frames/ altındaki frame PNG'lerini DAiSEE modeli ile değerlendirir.
 * Çıktı: evaluation.json (video bazında frame skorları; 4 sınıf: engagement seviyeleri)
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import * as tf from "@tensorflow/tfjs-node";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MODEL_DIR = path.join(__dirname, "daisee");
const FRAMES_DIR = path.join(__dirname, "frames");
const OUTPUT_JSON = path.join(__dirname, "evaluation.json");

// DAiSEE: 4 çıktı (örn. boredom, confusion, engagement, frustration seviyeleri 0-3)
const LABELS = ["boredom", "confusion", "engagement", "frustration"];

async function loadImageAsTensor(imagePath) {
  const buf = fs.readFileSync(imagePath);
  const tensor = tf.node.decodeImage(buf, 3);
  const resized = tf.image.resizeBilinear(tensor, [224, 224]);
  tensor.dispose();
  const normalized = resized.div(255.0);
  resized.dispose();
  const batched = normalized.expandDims(0);
  normalized.dispose();
  return batched;
}

function argmax(arr) {
  let max = arr[0], idx = 0;
  for (let i = 1; i < arr.length; i++) {
    if (arr[i] > max) { max = arr[i]; idx = i; }
  }
  return idx;
}

async function main() {
  const modelPath = path.join(MODEL_DIR, "model.json");
  if (!fs.existsSync(modelPath)) {
    console.error("Model bulunamadı:", modelPath);
    process.exit(1);
  }
  const model = await tf.loadGraphModel(`file://${modelPath}`);
  const inputName = Object.keys(model.inputs)[0] || "inputs";
  const results = { videos: {} };

  if (!fs.existsSync(FRAMES_DIR)) {
    fs.writeFileSync(OUTPUT_JSON, JSON.stringify({ videos: {} }, null, 2));
    console.log("frames/ yok, boş evaluation yazıldı.");
    return;
  }
  const videoDirs = fs.readdirSync(FRAMES_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  for (const videoName of videoDirs) {
    const dir = path.join(FRAMES_DIR, videoName);
    const files = fs.readdirSync(dir)
      .filter((f) => f.endsWith(".png"))
      .sort();
    const scores = [];
    for (const file of files) {
      const imgPath = path.join(dir, file);
      const input = await loadImageAsTensor(imgPath);
      const out = model.predict(input);
      input.dispose();
      const arr = (await out.dataSync());
      out.dispose();
      const pred = Array.from(arr);
      const classIdx = argmax(pred);
      scores.push({
        frame: file,
        scores: pred,
        dominant: LABELS[classIdx],
        level: classIdx,
      });
    }
    results.videos[videoName] = {
      frameCount: scores.length,
      frames: scores,
      summary: scores.reduce((acc, s) => {
        acc[s.dominant] = (acc[s.dominant] || 0) + 1;
        return acc;
      }, {}),
    };
  }

  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(results, null, 2), "utf-8");
  console.log("Değerlendirme yazıldı:", OUTPUT_JSON);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
