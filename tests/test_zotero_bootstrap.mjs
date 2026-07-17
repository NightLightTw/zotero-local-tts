import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const bootstrap = fs.readFileSync(
  new URL("../zotero-plugin/bootstrap.js", import.meta.url),
  "utf8"
);

class APIClient {}

let voiceResponseMode = "success";
const localRequests = [];

const originalGetReadAloudVoices = async function () {
  if (voiceResponseMode === "throw") {
    throw new Error("offline");
  }
  if (voiceResponseMode === "error") {
    return { error: "network" };
  }
  if (voiceResponseMode === "no-standard") {
    return {
      voices: { premium: [{ voices: { premium: { label: "Cloud Premium" } } }] },
      premiumCreditsRemaining: 50,
    };
  }
  return {
    voices: {
      standard: [{ voices: { cloud: { label: "Cloud Standard" } } }],
      premium: [{ voices: { premium: { label: "Cloud Premium" } } }],
    },
    standardCreditsRemaining: 100,
    premiumCreditsRemaining: 50,
    devMode: false,
  };
};
const originalGetReadAloudAudio = async function () {
  return { audio: "cloud-audio" };
};
APIClient.prototype.getReadAloudVoices = originalGetReadAloudVoices;
APIClient.prototype.getReadAloudAudio = originalGetReadAloudAudio;

const context = vm.createContext({
  Components: { interfaces: { nsIFile: class {} } },
  IOUtils: { readUTF8: async () => "test-token" },
  PathUtils: { join: (...parts) => parts.join("/") },
  Services: { dirsvc: { get: () => ({ path: "/Users/test" }) } },
  Zotero: {
    HTTP: {
      request: async (...args) => {
        localRequests.push(args);
        return { response: "local-audio" };
      },
    },
    Sync: { APIClient },
    debug: () => {},
    initializationPromise: Promise.resolve(),
    version: "9.0.6",
  },
});

vm.runInContext(bootstrap, context);
await vm.runInContext("startup()", context);

const client = new APIClient();
const response = await client.getReadAloudVoices();
assert.equal(response.voices.standard.length, 2);
const localConfiguration = response.voices.standard[0];
assert.equal(Object.keys(localConfiguration.voices).length, 9);
assert.deepEqual(Array.from(localConfiguration.locales["en-US"].default), [
  "zotero-local-qwen-aiden",
]);
assert.deepEqual(Array.from(localConfiguration.locales["en-US"].other), [
  "zotero-local-qwen-ryan",
]);
assert.equal(localConfiguration.locales["zh-CN"].default.length, 1);
assert.equal(localConfiguration.locales["zh-CN"].other.length, 4);
assert.equal(localConfiguration.locales["ja-JP"].default.length, 1);
assert.equal(localConfiguration.locales["ko-KR"].default.length, 1);
assert.equal(
  response.voices.standard[0].voices["zotero-local-qwen-aiden"].label,
  "Aiden (Qwen3-TTS, Local)"
);
assert.equal(response.voices.standard[1].voices.cloud.label, "Cloud Standard");
assert.equal(response.voices.premium[0].voices.premium.label, "Cloud Premium");
assert.equal(response.standardCreditsRemaining, 100);
assert.deepEqual(
  await client.getReadAloudAudio({}, "cloud"),
  { audio: "cloud-audio" }
);

const localAudio = await client.getReadAloudAudio(
  { text: "Local sentence." },
  "zotero-local-qwen-aiden"
);
assert.equal(localAudio.audio, "local-audio");
assert.equal(localRequests.length, 1);
assert.equal(localRequests[0][0], "POST");
assert.equal(localRequests[0][1], "http://127.0.0.1:8766/v1/audio/speech");
assert.equal(localRequests[0][2].headers.Authorization, "Bearer test-token");
assert.deepEqual(JSON.parse(localRequests[0][2].body), {
  model: "qwen3-customvoice-1.7b-8bit",
  voice: "Aiden",
  input: "Local sentence.",
  response_format: "wav",
  speed: 1.0,
});

const nativeVoices = {
  "zotero-local-qwen-ryan": "Ryan",
  "zotero-local-qwen-vivian": "Vivian",
  "zotero-local-qwen-serena": "Serena",
  "zotero-local-qwen-uncle-fu": "Uncle_Fu",
  "zotero-local-qwen-dylan": "Dylan",
  "zotero-local-qwen-eric": "Eric",
  "zotero-local-qwen-ono-anna": "Ono_Anna",
  "zotero-local-qwen-sohee": "Sohee",
};
for (const [voiceID, engineVoice] of Object.entries(nativeVoices)) {
  const result = await client.getReadAloudAudio({ text: "Native text." }, voiceID);
  assert.equal(result.audio, "local-audio");
  const payload = JSON.parse(localRequests.at(-1)[2].body);
  assert.equal(payload.voice, engineVoice);
}
assert.equal(localRequests.length, 9);

for (const mode of ["throw", "error"]) {
  voiceResponseMode = mode;
  const fallback = await client.getReadAloudVoices();
  assert.equal(fallback.voices.standard.length, 1);
  assert.equal(
    fallback.voices.standard[0].voices["zotero-local-qwen-aiden"].label,
    "Aiden (Qwen3-TTS, Local)"
  );
}

voiceResponseMode = "no-standard";
const missingStandard = await client.getReadAloudVoices();
assert.equal(missingStandard.voices.standard.length, 1);
assert.equal(missingStandard.voices.premium[0].voices.premium.label, "Cloud Premium");

await vm.runInContext("shutdown()", context);
assert.equal(APIClient.prototype.getReadAloudVoices, originalGetReadAloudVoices);
assert.equal(APIClient.prototype.getReadAloudAudio, originalGetReadAloudAudio);
